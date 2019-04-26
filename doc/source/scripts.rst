
Scripts
*******

Invirtualenv command line utilities.

invirtualenv
============

The `invirtualenv` command line tool is used to perform invirtualenv operations.  This script is meant to replace the
`create_package` and `deploy_virtualenv` scripts that are still provided for backwards compatibility.

invirtualenv usage
##################

The invirtualenv command takes a number of subcommands used to specify the invirtualenv function to perform::

    usage: invirtualenv [-h] [--deploy_conf DEPLOY_CONF]
                        {list_plugins,create_package_config,create_package,get_setting}
                        ...

    optional arguments:
      -h, --help            show this help message and exit
      --deploy_conf DEPLOY_CONF
                            Deploy configuration filename or url (default:
                            deploy.conf)

    command:
      {list_plugins,create_package_config,create_package,get_setting}
        list_plugins        List the installed invirtualenv plugins
        create_package_config
                            Generate the packaging configuration file
        create_package      Generate a package from a deployment configuration
        get_setting         Get a setting value from the configuration


.. _deploy_virtualenv:

deploy_virtualenv
=================

This script will create a new python virtual environment based on a
:ref:`deploy.conf` or :ref:`requirements.txt` file.  The script will default
to looking for
a :ref:`deploy.conf` file in the current directory for it's configuration
settings.

.. _deploy_virtualenv[Usage]:

Usage
#####

The :ref:`deploy_virtualenv` script has the following usage::

    usage: deploy_virtualenv [-h] [--python PYTHON] [--requirement REQUIREMENT]
                             [--virtualenvdir VIRTUALENVDIR]
                             [--virtualenvuser VIRTUALENVUSER]
                             [--virtualenvgroup VIRTUALENVGROUP]
                             [--virtualenvversion_package VIRTUALENVVERSION_PACKAGE]
                             [--install_os_packages INSTALL_OS_PACKAGES]
                             [name]

    Deploy a python application into a virtualenv

    positional arguments:
      name                  VirtualEnv name (default: public_mirror)

    optional arguments:
      -h, --help            show this help message and exit
      --python PYTHON, -p PYTHON
                            The Python interpreter to use, e.g.,
                            --python=python3.5 will use the python3.5 interpreter
                            to create the new environment. The default is the
                            interpreter that virtualenv was installed with.
                            (default: python2.7)
      --requirement REQUIREMENT, -r REQUIREMENT
                            Install from the given requirements file. This option
                            can be used multiple times. (default: [])
      --virtualenvdir VIRTUALENVDIR
                            Directory to build the virtualenv (default:
                            /var/tmp/virtualenv)
      --virtualenvuser VIRTUALENVUSER
                            The user to create the virtualenv (default: dhubbard)
      --virtualenvgroup VIRTUALENVGROUP
                            The group to create the virtualenv (default: )
      --virtualenvversion_package VIRTUALENVVERSION_PACKAGE
                            Version the virtualenv based on the version of a
                            package (default: public_mirror)
      --install_os_packages INSTALL_OS_PACKAGES
                            Install OS packages (default: False)


.. _deploy_virtualenv[Examples]:

Examples
########

.. _deploy_virtualenv[Examples]deploy.conf:

Deploying using deploy.conf
+++++++++++++++++++++++++++

The following example uses a :ref:`deploy.conf` file to do the following:

    * Creates a new python virtualenv with the following characteristics:
        * It is created in the `/var/tmp/virtualenv` directory
        * Uses a `python2.7` python interpreter
        * It has a base name of `public_mirror`
        * It has a version appended to the name based on the latest version of the `public_mirror` package in the python repo
        * The virtualenv is owned by unix user `pypimirror`

The example uses the following :ref:`deploy.conf` file::

    [global]
    ;######################################################################
    ; Global settings
    ;######################################################################
    ; The name of the virtualenv to create
    name = public_mirror

    ; The python interpreter to use for the virtualenv
    ; this will default to the python interpreter running the virtualenv
    ; command if it is not specified.
    basepython = python2.7

    ; Base directory to create virtualenv in
    virtualenv_dir = /var/tmp/virtualenv

    ; Use the version of a python package to determine the version component
    ; of the virtualenv.
    ; If no versions is found or specified the virtualenv will not have a
    ; version component in the name.
    virtualenv_version_package = public_mirror

    ; The user that should own the virtualenv.
    virtualenv_user = pypimirror

    ; When package manifest(s) to install into the virtualenv
    ; If none are specified all manifest will be deployed.
    ; Note:
    ;     It is generally a bad idea to use a deb and rpm manifest together.
    install_manifest = pip, rpm

    [pip]
    ;######################################################################
    ; PIP package settings
    ;######################################################################
    ; deps contains a list of python packages to install.
    ; It is recommended this be a concrete list such as what is returned
    ; using the 'pip freeze' command.
    ; Each line must be indented.
    deps:
        astroid==1.4.4
        colorama==0.3.6
        eventlet==0.18.2
        future==0.14.3
        greenlet==0.4.9
        IPy==0.83
        keyring==8.4
        lazy-object-proxy==1.2.1
        mccabe==0.4.0
        pkginfo==1.2.1
        pluggy==0.3.1
        py==1.4.31
        pycrypto==2.6.1
        pylint==1.5.4
        PyYAML==3.11
        requests==2.9.1
        six==1.10.0
        wrapt==1.10.6

    [rpm]
    ;######################################################################
    ; rpm package settings
    ;######################################################################
    deps:
        libcrypto-dev

The resulting output from running the :ref:`deploy_virtualenv` command in the
same directory as the :ref:`deploy.conf` is::

    # deploy_virtualenv

    *******************************************************************
    Parsing the configuration
    *******************************************************************

    *******************************************************************
    Getting version based on package 'public_mirror' from the repo
    *******************************************************************
    Using version: 0.0.13

    *******************************************************************
    Installing rpm packages
    *******************************************************************
    libcrypto

    *******************************************************************
    Building virtualenv
    *******************************************************************
    You are using pip version 7.1.2, however version 8.0.2 is available.
    You should consider upgrading via the 'pip install --upgrade pip' command.
    New python executable in /var/tmp/virtualenv/public_mirror_0.0.13/bin/python2.7
    Also creating executable in /var/tmp/virtualenv/public_mirror_0.0.13/bin/python
    Installing setuptools, pip, wheel...done.
    Creating /var/tmp/virtualenv/public_mirror_0.0.13/conf directory
    Creating /var/tmp/virtualenv/public_mirror_0.0.13/logs directory

    *******************************************************************
    Installing python package dependencies
    *******************************************************************
    Installing requirements from requirements file: /tmp/tmphBEO0g into virtualenv /var/tmp/virtualenv/public_mirror_0.0.13 as user None
    Current user is: root
    Current uid: 0, Effective uid: 0

    *******************************************************************
    Fixing file ownership
    *******************************************************************


This is the virtualenv that got created by the last command::

    # ls -lh /var/tmp/virtualenv/
    total 0
    drwxrwxr-x 1 pypimirror pypimirror 88 Feb 19 00:38 public_mirror_0.0.13
    [root@6b7d38db3855 dhubbard]#


.. _deploy_virtualenv[Examples]cli:

Creating a virtualenv using CLI arguments
+++++++++++++++++++++++++++++++++++++++++

The following example creates a new python virtualenv with the following characteristics:

    * It is created in the /tmp directory
    * It has a base name of invirtualenv
    * It has a version appended to the virtualenv based on the latest version of the `invirtualenv` python package (1.1.62)
    * The virtualenv is owned by the unix user dhubbard

The following requirements.txt file is used::

        cov-core==1.15.0
        coverage==4.0.1
        future==0.15.2
        nose==1.3.7
        nose-cov==1.6
        requests==2.8.1
        virtualenv==13.1.2
        wheel==0.24.0


This is what this example looks like::

    airreport-lm:invirtualenv dhubbard$ deploy_virtualenv.py --virtualenvdir /tmp --virtualenvversion_package invirtualenv --virtualenvuser dhubbard -r requirements.txt invirtualenv
    *******************************************************************
    Building virtualenv
    *******************************************************************
    You are using pip version 7.0.3, however version 8.0.2 is available.
    You should consider upgrading via the 'pip install --upgrade pip' command.
    Using real prefix '/Library/Frameworks/Python.framework/Versions/2.7'
    New python executable in invirtualenv_1.1.62/bin/python
    Installing setuptools, pip, wheel...done.
    Creating /tmp/invirtualenv_1.1.62/conf directory
    Creating /tmp/invirtualenv_1.1.62/logs directory

    *******************************************************************
    Installing python package dependencies
    *******************************************************************
    Installing requirements from requirements file: ['requirements.txt'] into virtualenv /tmp/invirtualenv_1.1.62 as user None
    Current user is: dhubbard
    Current uid: 58157, Effective uid: 58157
    The directory '~/.cache' or its parent directory is not owned by the current user and caching wheels has been disabled. check the permissions and owner of that directory. If executing pip with sudo, you may want sudo's -H flag.

    *******************************************************************
    Fixing file ownership
    *******************************************************************

The resulting virtualenv directory has been created, owned by the specified user::

    drwxrwxr-x  10 dhubbard  wheel  340 Feb 11 14:58 /tmp/invirtualenv_1.1.62


.. _create_package:

create_package
==============

The :ref:`create_package` script creates packages of various types that contain the python application deployed within a virtualenv.

.. _create_package[Usage]:

Usage
#####

The :ref:`create_package` script has the following usage::

    usage: create_package [-h] [--package_type {rpm, tar}]

    optional arguments:
      -h, --help            show this help message and exit
      --package_type {rpm}
                            Type of package to create
