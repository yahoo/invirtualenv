
InVirtualEnv
============

The invirtualenv package contains scripts for deploying
applications written in Python inside Python virtualenv.

These included scripts can:

* Create native packages via plugins that contain a Python application installed inside.  Currently there are plugins to create rpms and docker containers.
* Create a specified operating system platform using an RPM package list.
* Create a Python virtualenv, when running as root the virtualenv can be
  deployed so that it can be manipulated by another user.
* Deploy Python packages into the virtualenv from a pip
  requirements file.

The script can be configured using command line arguments or all configuration
can be defined in a single deploy.conf file.
