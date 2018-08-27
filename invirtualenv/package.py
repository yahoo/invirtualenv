# Copyright (c) 2016, Yahoo Inc.
# Copyrights licensed under the BSD License
# See the accompanying LICENSE.txt file for terms.

"""
Functions for managing packaging
"""
import os
import platform
from xml.etree import ElementTree
import subprocess

try:  # pragma: no cover
    import configparser as ConfigParser
except ImportError:  # pragma: no cover
    import ConfigParser

import requests

from .exceptions import BuildException
from .utility import display_header
from distutils.version import LooseVersion


def package_scripts_directory():
    """
    Get the package scripts directory

    Returns
    str
        The path to the directory containing the package scripts
    """
    module_directory = os.path.dirname(__file__)
    script_directory = os.path.join(
        module_directory,
        'package_scripts'
    )
    return script_directory


def strip_from_end(text, suffix):
    """
    Strip a substring from the end of a string

    Parameters
    ----------
    text : str
        The string to be evaluated

    suffix : str
        The suffix or substring to remove from the end of the text string

    Returns
    -------
    str
        A string with the substring removed if it was found at the end of the
        string.
    """
    if not text.endswith(suffix):
        return text
    return text[:len(text)-len(suffix)]


def package_versions(package, pypi_url=None):
    """
    Get all versions of a package from pypi

    Parameters
    ----------
    package : str
        The python package to search for

    pypi_url : str, optional
        The pypi URL to send the request to, defaults to the production
        pypi endpoint.

    Returns
    -------
    list
        A list of all packages found on pypi.  The list will be
        empty if there were no versions found.
    """
    if pypi_url:  # pragma: no cover
        url = pypi_url
    else:
        index_url = 'https://pypi.python.org/simple'
        if os.path.exists('/etc/pip.conf'):  # pragma: no cover
            cfg = ConfigParser.SafeConfigParser({'index-url': index_url})
            cfg.read('/etc/pip.conf')
            index_url = cfg.get('global', 'index-url')
        url = '%s/%s/' % (index_url, package)
    versions = []
    response = requests.get(url)
    if response.status_code in [404]:  # pragma: no cover
        return []
    result = response.text
    tree = ElementTree.fromstring(result)
    for element in tree.findall('.//a/[@rel="internal"]'):
        possible_package = element.text
        if possible_package.endswith('.tar.gz'):
            possible_package = strip_from_end(possible_package, '.tar.gz')
            possible_package = possible_package.split('-')
            version = possible_package[-1]
            versions.append(version)

    versions.sort(key=LooseVersion)
    return versions


def latest_package_version(package):
    """
    Get the latest version number for a package

    Parameters
    ----------
    package : str
        Package to get the latest version of

    Returns
    -------
    str
        Latest package version or an empty string if no versions are found
    """
    versions = package_versions(package)
    if not versions:
        return ''
    return versions[-1]


def install_prereq_packages(test=False):  # pragma: no cover
    """
    Install packages required to build python

    Parameters
    ----------
    test: bool, optional
        Don't run the actual command, if True
    """
    resulting_files = [
        '/usr/bin/gcc',
        '/usr/bin/make'
    ]
    needed_packages = [
        'gcc',
        'make',
        'git',
        'libffi',
        'libffi-devel',
        'gdb',
        'glibc-devel',
        'libstdc++-devel',
        'libcom_err-devel',
        'krb5-devel',
        'openssl-devel',
        'gettext-devel',
        'gdbm-devel',
        'zlib-devel',
        'libsepol-devel',
        'sqlite-devel',
        'tk-devel',
        'expat-devel',
        'readline-devel',
        'ncurses-devel',
        'bzip2-devel',
        'xz-devel',
        'gmp-devel',
        'mysql-devel',

        # Packages not in RHEL releases before RHEL6
        'db4-devel',
        'libpcap-devel',
    ]
    if platform.system() in ['Darwin']:
        print('No prereq packages defined for platform %s' % platform.system())
        return
    redhat_release = '7.0'
    if os.path.exists('/etc/redhat-release'):
        redhat_release = open('/etc/redhat-release').readlines()[0].strip().split()[-2]
    display_header('Installing build system needed for build on Redhat %s' % redhat_release)
    display_header('Installing additional build dependencies')
    if not test:  # pragma: no cover
        subprocess.check_output(['yum', '-y', 'install'] + needed_packages)

    display_header('Verifying needed dependencies where installed')
    for filename in resulting_files:
        if not test and not os.path.exists(filename):  # pragma: no cover
            raise BuildException('Required file %s is missing' % filename)

    if redhat_release.startswith('6'):
        display_header('Fixing the user .gitconfig to work with git < 1.8')
        gitconfig = os.path.exists(os.path.expanduser('~/.gitconfig'))
        if os.path.exists(gitconfig):
            old_git_config = []
            with open(gitconfig) as file_handle:
                old_git_config = file_handle.read().split('\n')

            with open(gitconfig, 'w') as file_handle:
                for line in old_git_config:
                    if 'default=simple' not in line.replace(' ', ''):
                        file_handle.write(line + '\n')
