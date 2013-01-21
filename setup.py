from setuptools import setup, find_packages
import os.path
import imp


ROOT = os.path.abspath(os.path.dirname(__file__))

def read(fname):
    """Read a file relative to the repository root"""
    return open(os.path.join(ROOT, fname)).read()

def version():
    """Return the version number from supervise.py"""
    file, pathname, description = imp.find_module('supervise', [ROOT])
    return imp.load_module('supervise', file, pathname, description).__version__

VERSION = version()
setup(
    name="supervise",
    version=VERSION,
    packages=find_packages(),
    description="Tools for communicating with runit / daemontools supervisors.",
    long_description=read("README.rst"),

    install_requires=[],
    setup_requires=['unittest2'],
    author='Andres J. Diaz',
    author_email='ajdiaz@connectical.com',
    maintainer='Peter Ruibal',
    maintainer_email='ruibalp@gmail.com',
    #license='ISC',
    keywords='supervise runit daemontools',
    url='http://github.com/fmoo/python-supervise',
    download_url='https://github.com/fmoo/python-supervise/archive/%s.tar.gz' % VERSION,

    #test_suite="tests",

    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Software Development :: Libraries",
        #"License :: OSI Approved :: ISC License (ISCL)",
    ],
)
