# Copyright (c) 2016, Yahoo Inc.
# Copyrights licensed under the BSD License
# See the accompanying LICENSE.txt file for terms.

"""
Functions for managing packaging
"""
from collections import defaultdict
from distutils.version import LooseVersion, StrictVersion
from html.parser import HTMLParser
import logging
import os
import platform
import subprocess  # nosec
from typing import DefaultDict, Dict, List, Optional

try:  # pragma: no cover
    import configparser as ConfigParser
except ImportError:  # pragma: no cover
    import ConfigParser

from defusedxml import ElementTree
import pkg_resources
import requests

from .exceptions import BuildException
from .utility import display_header
from distutils.version import LooseVersion


logger = logging.getLogger(__name__)


class HTMLLinkParser(HTMLParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.href_list = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for name, value in attrs:
                if name == "href":
                    self.href_list.append(value)


def get_index_url():
    index_url = 'https://pypi.python.org/simple'
    if os.path.exists('/etc/pip.conf'):  # pragma: no cover
        cfg = ConfigParser.SafeConfigParser({'index-url': index_url})
        cfg.read('/etc/pip.conf')
        index_url = cfg.get('global', 'index-url')
    return index_url.rstrip('/')


def package_files(package: str, pypi_url: str='https://pypi.org') -> List[str]:
    if not pypi_url:
        pypi_url = get_index_url()
    name = pkg_resources.safe_name(package)
    url = pypi_url + '/simple/' + package + '/'
    parser = HTMLLinkParser()

    # Stream the index
    req = requests.get(url, stream=True)
    for line in req.iter_lines():
        line = line.decode(errors='ignore')
        parser.feed(line)

    files = []
    for filename in parser.href_list:
        filename = os.path.basename(filename).split('#')[0]
        files.append(filename)
    return files


def package_type_versions(package: str, pypi_url: str='https://pypi.org', require_strict: bool=False) -> Dict[str, list]:
    if not pypi_url:
        pypi_url = get_index_url()

    package_releases: DefaultDict[str, List] = defaultdict(lambda: [], {'tar.gz': [], 'whl': [], 'zip': []})
    name = pkg_resources.safe_name(package)

    sorted_key = StrictVersion if require_strict else LooseVersion

    for filename in package_files(package=package, pypi_url=pypi_url):
        # Separate the releases by extension
        for ext in package_releases.keys():  # pragma: no cover
            if filename.endswith('.' + ext):
                filename = filename[len(name) +1 :-(len(ext) + 1)]
                if ext == 'whl':
                    split_name = filename.split('-')
                    filename = '-'.join(split_name[:-3])
                    tags = '-'.join(split_name[-3:])
                    package_releases[f'{ext}-{tags}'].append(filename)
                package_releases[ext].append(filename)
                break

    # Sort the results
    for value in package_releases.values():
        try:
            sorted(value, key=sorted_key)
        except ValueError as error:
            if not require_strict:
                logger.info(f'Invalid package version {value!r} found in the index using strict versioning, falling back to loose versioning')
                sorted( value, key=LooseVersion)
            else:
                raise error
    return package_releases


def package_versions(package: str, pypi_url: str='https://pypi.org', require_strict: bool=False) -> List[str]:
    if not pypi_url:
        pypi_url = get_index_url()

    all_versions = set()
    for key, value in package_type_versions(package, pypi_url=pypi_url, require_strict=require_strict).items():
        all_versions.update(value)
    return list(all_versions)


def existing_package(
        package: str, version: str, package_types: Optional[List[str]]=None, pypi_url: str='https://pypi.org'
) -> bool:
    if not pypi_url:
        pypi_url = get_index_url()

    if not package_types:  # pragma: no cover
        package_types = ['tar.gz', 'whl', 'zip']

    package_releases = package_type_versions(package, pypi_url=pypi_url)

    for package_type in package_types:
        if package_type not in package_releases.keys():
            continue
        versions = list(package_releases[package_type])
        if version in versions:
            return True

    return False


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
        subprocess.check_output(['yum', '-y', 'install'] + needed_packages)  # nosec

    display_header('Verifying needed dependencies where installed')
    for filename in resulting_files:
        if not test and not os.path.exists(filename):  # pragma: no cover
            raise BuildException('Required file %s is missing' % filename)

    if redhat_release.startswith('6'):
        display_header('Fixing the user .gitconfig to work with git < 1.8')
        gitconfig = os.path.expanduser('~/.gitconfig')
        if os.path.exists(gitconfig):
            old_git_config = []
            with open(gitconfig) as file_handle:
                old_git_config = file_handle.read().split('\n')

            with open(gitconfig, 'w') as file_handle:
                for line in old_git_config:
                    if 'default=simple' not in line.replace(' ', ''):
                        file_handle.write(line + '\n')
