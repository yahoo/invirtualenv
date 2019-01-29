
Install
*******

The :ref:`invirtualenv` utilities are part of a python package which can be
installed using pip.

Quickstart
==========

Install the package using the python pip package utility::

    pip install -U invirtualenv


Platform
========

Some of the scripts provided by the :ref:`invirtualenv` package have enhanced
functionality depending on the platform they are run on.

On systems that support rpm, the following rpm packages are required to utilize
the rpm package support in the :ref:`create_package` script.::

    rpm-build

The Docker container build requires the :ref:`docker` command has been installed and working.
