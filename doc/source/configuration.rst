Configuration Settings
**********************

The :ref:`deploy_virtualenv` script can use two different configuration files:
:ref:`deploy.conf` and :ref:`requirements.txt` these files have different
functionality and usage.

.. _deploy.conf:

deploy.conf - Deployment configuration file
===========================================

The :ref:`deploy.conf` file allows for setting all configuration arguments in
a single file.  This allows running the script without any other command line
arguments.

The same file can be used for deployment and generation of deployment packages
in multiple packaging formats.  Current supported deployment packaging formats
are: rpm and docker containers.

The :ref:`deploy.conf` file is a Python :py:mod:`ConfigParse` format
configuration file.  This file consists of sections which are deliminated by
square brackets. Inside each section are key/value fields.  Multi-Line
values can be defined by indenting subsequent lines.

The :ref:`deploy.conf` file has at least 3 possible sections, all of which are
optional: global, pip, rpm.

The :ref:`deploy.conf` supports :ref:`jinja2` template format substitutions for
values of environment variables.  This allows setting values based on
environment variable values.  I.E. setting the version based on the
BUILD_NUMBER environment variable provided by the CI pipeline for example.

.. _[global]:

global settings
###############

The :ref:`[global]` section of the :ref:`deploy.conf` defines a number of
settings.  All of which are optional.  These settings act as the default
values if they are not set in other sections.

.. _[global]name:

name
~~~~
The :ref:`[global]name` setting is used to define the basename of the
virtualenv to be created.

.. _[global]basepython:

basepython
~~~~~~~~~~

The :ref:`[global]basepython` setting is used to define the python interpreter
inside the virtualenv.  If this setting is not specified it will default to the
python interpreter that runs the virtualenv command.

.. _[global]install_manifest:

install_manifest
~~~~~~~~~~~~~~~~

The :ref:`[global]install_manifest` setting specifies a comma separated list
of manifests to install.  If this setting is not set all package manifests
(lists of packages) that will be installed.

** NOTE: It is generally not a good idea to mix multiple types of platform
package manifests.  Such as using both rpm and tar **

.. _[global]install_os_packages:

install_os_packages
~~~~~~~~~~~~~~~~~~~

The :ref:`[global]install_os_packages` setting causes the script to attempt to
install the rpm package resources needed to install Python sdist format
packages.

.. _[global]virtualenv_dir:

virtualenv_dir
~~~~~~~~~~~~~~

The :ref:`[global]virtualenv_dir` setting specifies the directory that will
hold the virtualenv that is created.  This directory needs to be writable by
the user running the script.

.. _[global]version:

version
~~~~~~~

This setting will set the version string the the value specified.

The example below the version string is specified to be based on the
BUILD_NUMBER environment variable, defaulting to '0.0.0' if the BUILD_NUMBER
is not set.  In the example below if the BUILD_NUMBER was set to 15 the
version would be '0.0.15'::


   version = 0.0.{{BUILD_NUMBER|default('0')}}


.. _[global]virtualenv_version_package:

virtualenv_version_package
~~~~~~~~~~~~~~~~~~~~~~~~~~

This setting will lookup the most recent version of the package specified and
append that version number to the end of the virtualenv name.  This allows
versioning the virtualenvs based on a specific package version.

For example, if the most recent version of the public_mirror package is 0.39.0
and the virtualenv was created with the following settings::

    name = mirror
    virtualenv_version_package = public_mirror

The virtualenv will be named ** mirror_0.39.0 **

.. _[global]virtualenv_user:

virtualenv_user
~~~~~~~~~~~~~~~

This setting specifies the unix username that should own the created
virtualenv.

This setting requires the following:

    * This script is being run by a user that has the privileges to change the
    ownership to the user specified (generally root)
    * The user specified has been created on the system.

.. _[global]virtualenv_group:

virtualenv_group
~~~~~~~~~~~~~~~~

This setting specifies the unix group of the created virtualenv.

This setting requires the following:

    * This script is being run by a user that has the privileges to change the
      group to the user specified (generally root)
    * The group specified has been created on the system.

.. _[pip]:

pip package manifest
####################

This configuration section allows defining settings related to the installation
of python packages that are installed using the `pip` tool.   As part of a pip
package manifest.

This section is used to define the python packages to install.

.. _[pip]deps:

deps
~~~~

The deps section contains a list of python packages to install.  The format for
the deps is the same as the format of a `pip` requirements file.

.. _[rpm]:

rpm package manifest
####################

The [rpm] configuration section allows defining package manifests (list of packages)
of rpm packages installed using the yum tool.

These is section defines a package manifest of rpm packages to install prior to
installing the python packages.

Note:

    rpm package installations are not atomic and once installed some package
    dependencies can block uninstall or upgrade of certain packages.  As a
    result a rpm install failure can leave the system in a different package
    state than when the script run started.

.. _[rpm]deps:

deps
~~~~

This section is a list of rpm packages to install.

docker_container packaging (creation)
#####################################

The [docker_container] section contains the settings used to create a docker
container containing the python application in a virtualenv.  This section allows
for adding settings used to create the docker container.

The docker plugin will generate basic sane container based on the defaults and values
in the global section of the configuration.

This section can be used to set docker specific settings such as commands to use for
healthchecks of the created docker container.


add
~~~

base_image
~~~~~~~~~~

default=ubuntu:17.10

container_name
~~~~~~~~~~~~~~

copy
~~~~

deb_deps
~~~~~~~~

A manifest of debian packages to install into the container prior to creating the
python virtualenv.

entrypoint
~~~~~~~~~~

env
~~~

expose
~~~~~~

files
~~~~~

healthcheck
~~~~~~~~~~~

This is the healthcheck script to run in the container.

label
~~~~~

A list of labels to be applied to the container.

rpm_deps
~~~~~~~~

A manifest of rpm packages to install into the container prior to creating the python
virtualenv.

run_before
~~~~~~~~~~

A list of shell commands to run before creating the python virtualenv inside the container.

run_after
~~~~~~~~~

A list of shell commands to run after creating the python virtualenv inside the container.

setenv
~~~~~~

Environment variables to set when creating the container.

stopsignal
~~~~~~~~~~

user
~~~~

volume
~~~~~~

A list of volume mappings to use with the container.


rpm packaging
#############
The [rpm_package] section defines settings related to the creation of rpm packages.
The settings in this section will override the default values from the global settings
for rpm package generation only.

.. _[rpm_package]deps:

deps
~~~~

This is a manifest (list of packages) to be listed as dependencies of the created
rpm package.


Note::

    This should include the packages that contain the python interpreter
    and virtualenv commands to use to deploy the virtualenv when the created package
    is installed.

Example deploy.conf
###################

.. include:: ../../examples/deploy.conf
   :literal:

.. _requirements.txt:

requirements.txt
================

The :ref:`requirements.txt` file is a pip format :ref:`requirements.txt` file and only specifies the python packages to be installed in the virtualenv.
