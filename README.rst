Python supervise
----------------
This module provide a methods to handle runit [1]_ or daemontools [2]_ based
supervised services, using the control file provided. Here are a small
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
