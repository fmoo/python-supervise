#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
Python supervise
----------------
This module provide a methods to handle runit [1]_ or daemontools [2]_ based
supervised services, using the control file provided.  Here is a small
example::

    >>> import supervise
    >>> s = supervise.Service('test')
    >>> print s.status()
    {'action': None, 'status': 0, 'uptime': 300L, 'pid': None}
    >>> s.start()
    >>> print s.status()
    {'action': None, 'status': 1, 'uptime': 3L, 'pid': 27450}

Read the manpage of runsv(8) for more information. Also read the
documentation for :class:`ServiceStatus` to known how to parse status
information.

History
=======

Last month I needed to install runit in some servers to supervise a couple
of services. Unfortunately my management interface cannot handle the
services anymore, so I decided to write a small module in python to solve
this handicap, and that is the result!.

With this module you can handle in python environment a number of runit
scripts. I think that this might be work for daemontools too, but I do not
test yet. Let's see an example::

    >>> import supervise
    >>> c = supervise.Service("/var/service/httpd")
    >>> print s.status()
    {'action': 'normal', 'status': 'up', 'uptime': 300L, 'pid': None}
    >>> if s.status()['status'] == supervise.STATUS_DOWN: print "service down"
    service down
    >>> s.start()
    >>> if s.status()['status'] == supervise.STATUS_UP: print "service up"
    service up


Personally I use this module with rpyc library to manage remotely the
services running in a host, but it too easy making a web interface, for
example using bottle::

    import supervise
    import simplejson
    from bottle import route, run

    @route('/service/status/:name')
    def service_status(name):
        return simplejson.dumps( supervise.Service("/var/service/" +
            name).status() )

    @route('/service/up/:name')
    def service_up(name):
        c = supervise.Service("/var/service/" + name)
            c.start()
        return "OK UP"


    @route('/service/down/:name')
    def service_down(name):
        c = supervise.Service("/var/service/" + name)
            c.down()
        return "OK DOWN"


    if __name__ == "__main__":
        run()


Now you can stop your service just only point your browser
http://localhost/service/down/httpd (to down http service in this case).

Enjoy!

.. [1] http://smarden.org/runit/
.. [2] http://cr.yp.to/daemontools.html

:author: Andres J. Diaz <ajdiaz@connectical.com>
:date:   2009-11-21
"""

__version__ = '1.0'

import struct

DEFAULT_SERVICE_DIR = "/var/service" # change for daemontools

try:
    import os
    DEFAULT_SERVICE_DIR = os.getenv("SERVICE_DIR")
except:
    pass

DEFAULT_EPOCH = 4611686018427387914L

STATUS_DOWN   = 0x00
STATUS_UP     = 0x01
STATUS_FINISH = 0x02

NORMALLY_DOWN = 0x00
NORMALLY_UP   = 0x01
PAUSED        = 0x02
WANT_UP       = 0x11
WANT_DOWN     = 0x10
GOT_TERM      = 0x09

class ServiceStatus(object):
    """ This class models a status return struct from status file from
    supervisor. """
    def __init__(self, *args, **kwargs):
        """
        You can intialize this function passing arguments in the form
        *argument*=*value*, these properties will be stored on object.
        Example::

            >>> s = ServiceStatus( status=STATUS_DOWN )
            >>> s = ServiceStatus( pid=676 )

        You can query the status via a normal get attribute::

            >>> print s.pid
            >>> 676

        You cast safely this object to a dict to get the returned values.
        Usually status contains the keys:

        :param status: can be DOWN, UP or FINISH
        :param action: can be NORMALLY_UP, NORMALLY_DOWN, GOT TERM, PAUSED
        :param pid: contain the pid of the service if its not down, otherwise
            an exception is raised.
        :param time: return a timestamp when last action performs.
        """
        map(lambda x: setattr(self,x[0],x[1]), kwargs.items())

    def _status2str(self, status):
        if not status:
            return "unknown"
        if status == STATUS_DOWN:
            return "down"
        if status == STATUS_UP:
            return "up"
        if status == STATUS_FINISH:
            return "finish"

    def _action2str(self, action):
        if not action:
            return "normal"
        if action == NORMALLY_DOWN:
            return "normally down"
        if action == NORMALLY_UP:
            return "normally up2"
        if action == PAUSED:
            return "paused"
        if action == WANT_UP:
            return "want up"
        if action == WANT_DOWN:
            return "want down"
        if action == GOT_TERM:
            return "got term"

    def __iter__(self):
        for item in filter(lambda x: x[0]!='_', dir(self)):
            yield ( item, getattr(self,item,None) )

    def __str__(self):
        _d = dict()
        for item in filter(lambda x: x[0]!='_', dir(self)):
            if item == "status":
                _d["status"] = self._status2str(getattr(self,item,None))
            elif item == "action":
                _d["action"] = self._action2str(getattr(self,item,None))
            else:
                _d[item] = getattr(self,item,None)
        return str(_d)

class Service(object):
    """ This class manage a basic runit service with control pipe. """

    def __init__(self, service):
        """ Create a new Service object for runit

        :param service: must be a valid service name or a path to service
            directory. """

        self.up   = self.start
        self.down = self.stop
        self.hup  = self.hangup

        # Alias to send custom signal to backend control file.
        self.custom = self._signal

        if service[0] == "/":
            self.service = service
        else:
            self.service = DEFAULT_SERVICE_DIR + "/" + service

        self._control = self.service + "/supervise/control"
        self._status  = self.service + "/supervise/status"

    def start(self):
        """ Up the service """
        self._signal("u")

    def pause(self):
        """ If the service is running, send it a STOP signal. """
        self._signal("p")

    def alarm(self):
        """ If the service is running, send it an ALRM signal. """
        self._signal("a")

    def terminate(self):
        """ If the service is running, send it a  TERM signal. """
        self._signal("t")

    def exit(self):
          """ If  the  service  is running, send it a TERM signal, and
          then a CONT signal.  Do not restart the service.  If the service
          is down, and no log service exists, runsv exits.  If the service
          is down and a log service  exists,  runsv  closes  the  standard
          input of the log service, and waits for it to terminate.  If the
          log service is down, runsv exits.  This command is ignored if it
          is given to service/log/supervise/control."""
          self._signal("x")

    def kill(self):
        """ If the service is running, send it a  KILL signal. """
        self._signal("k")

    def user1(self):
        """ If the service is running, send it an USR1 signal. """
        self._signal("1")

    def user2(self):
        """ If the service is running, send it an USR2 signal. """
        self._signal("2")

    def quit(self):
        """ If the service is running, send it an QUIT signal. """
        self._signal("q")

    def interrupt(self):
        """ If the service is running, send it an INT signal. """
        self._signal("i")

    def hangup(self):
        """ If the service is running, send it a HUP signal. """
        self._signal("h")

    def cont(self):
        """ If the service is running, send it a CONT signal. """
        self._signal("c")

    def once(self):
        """ If the service is not running, start it.  Do not  restart
        it if it stops. """
        self._signal("o")

    def stop(self):
        """ Down the service """
        self._signal("d")

    def _signal(self, signal):
        f = open(self._control,"w+")
        f.write(signal)
        f.close()

    def status(self):
        """ Read the status of a service using status binary form. Returns
        an object :class:`ServiceStatus` with properly information.

        This function handle the follwing status code to be parsed:

        :param status: must be one numerical code to identify the service status,
            STATUS_UP(1), STATUS_DOWN(0) or STATUS_FINISH(2).
        :param action: print the action in what supervisor is working to change
            the state, it can be NORMALLY_UP(1), NORMALLY_DOWN(0),
            PAUSED(2), WANT_UP(17), WANT_DOWN(16), GOT_TERM(9). If no work
            in progress this value is setted to None.
        :param pid: contains the numeric PID of the service process, must be None
            if process status is STATUS_DOWN.
        :param uptime: contain the number of seconds since the last status is
            reached (means downtime for STATUS_DOWN).

        """
        byte = struct.Struct("20B")
        normallyup = 0

        s = open(self._status,"rb").read(20)
        s = byte.unpack_from(s)

        try:
            f = open(self.service + "/down","r")
            f.close()
        except IOError:
            # TODO catch ENOENT versus other errors
            normallyup = 1

        pid = s[15]
        pid <<=8; pid += s[14]
        pid <<=8; pid += s[13]
        pid <<=8; pid += s[12]

        if pid:
            if s[19] == 1: status = STATUS_UP
            if s[19] == 2: status = STATUS_FINISH
        else:
            pid = None
            status = STATUS_DOWN

        action = None # never happend
        if pid and not normallyup: action = NORMALLY_DOWN
        if not pid and normallyup: action = NORMALLY_UP
        if pid and s[16]: action = PAUSED
        if not pid and s[17] == 'u': action = WANT_UP
        if pid and s[17] == 'd': action = WANT_DOWN
        if pid and s[18]: action = GOT_TERM

        # When is now?
        try:
            import time
            n = long(time.time()) + DEFAULT_EPOCH

            # Get timestamp (8B = seconds)
            x = s[0];
            x <<= 8; x += s[1];
            x <<= 8; x += s[2];
            x <<= 8; x += s[3];
            x <<= 8; x += s[4];
            x <<= 8; x += s[5];
            x <<= 8; x += s[6];
            x <<= 8; x += s[7];

            x = 0 if n < x else (n - x)
        except ImportError:
            return ServiceStatus( status=status, pid=pid, action=action )

        return ServiceStatus( status=status, pid=pid, action=action,
                uptime=x )
