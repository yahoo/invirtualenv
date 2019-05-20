[![Build Status](https://cd.screwdriver.cd/pipelines/2835/badge)](https://cd.screwdriver.cd/pipelines/2835)
[![Documentation](https://readthedocs.org/projects/invirtualenv/badge/?version=latest)](https://invirtualenv.readthedocs.io/en/latest/?badge=latest)
[![Code Coverage](https://codecov.io/gh/yahoo/invirtualenv/branch/master/graph/badge.svg)](https://codecov.io/gh/yahoo/invirtualenv)
[![Downloads](https://pepy.tech/badge/invirtualenv)](https://pepy.tech/project/invirtualenv)

# InVirtualEnv

The invirtualenv package contains scripts for deploying applications written in Python onto operating systems.

These included scripts can:

* Create native packages via plugins that contain a Python application installed inside.  Currently there are plugins to create rpms and docker containers.
* Create a specified operating system platform using an RPM package list.
* Create a Python virtualenv, when running as root the virtualenv can be deployed so that it can be manipulated by another user.
* Deploy Python packages into the virtualenv from a pip requirements file.
* Create a docker container with the application installed.

The script can be configured using command line arguments or all configuration
can be defined in a single deploy.conf file.
