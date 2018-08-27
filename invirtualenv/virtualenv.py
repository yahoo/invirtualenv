# Copyright (c) 2016, Yahoo Inc.
# Copyrights licensed under the BSD License
# See the accompanying LICENSE.txt file for terms.

"""
Functions for creating and managing python virtual environments
"""
from __future__ import print_function
import getpass
import hashlib
import json
import logging
import os
from pwd import getpwnam
import shutil
import subprocess
import sys

try:
    import venv
    BUILTIN_VENV = True
except ImportError:
    BUILTIN_VENV = False

from .exceptions import BuildException
from .utility import change_uid_gid, chown_recursive, which


logger = logging.getLogger(__name__)  # pylint: disable=C0103


def default_virtualenv_directory():
    """
    Get the default virtualenv directory for the current system/platform

    Returns
    -------
    str
        The path to the default virtualenv directory
    """
    if os.path.exists('/var/tmp'):
        return '/var/tmp/virtualenv'

    return '/tmp/virtualenv'


def virtualenv_command(install_virtualenv=False):
    """
    Return the virtualenv command

    Parameters
    ----------
    install_virtualenv : bool
        If True, Install virtualenv if necessary.  default=False

    Returns
    -------
    str
        Path to the virtualenv command
    """
    if not hasattr(sys, 'frozen'):
        if install_virtualenv:
            packages = os.popen('pip freeze').read()
            if 'virtualenv' not in packages:
                subprocess.check_output(['pip', 'install', 'virtualenv'])
    return which('virtualenv')


def virtualenv_bin_file_hashes(virtualenv_dir):
    """
    Calculate a hash of all files in the virtualenv bin directory
    Parameters
    ----------
    virtualenv_dir : str
        The root directory of the virtualenv to operate on
    Returns
    -------
    dict:
        Key = Filename, value = hash
    """
    bin_dir = os.path.join(virtualenv_dir, 'bin')
    if not os.path.exists(bin_dir):
        return
    result = {}
    for filename in os.listdir(bin_dir):
        full_filename = os.path.join(bin_dir, filename)
        if os.path.isdir(full_filename):
            continue
        filehash = hashlib.sha256()
        with open(full_filename, 'rb') as handle:
            filehash.update(handle.read())
        result[filename] = filehash.hexdigest()
    return result


def remove_virtualenv(name, directory=None):
    """
    Remove a virtualenv from a directory
    :param name:
    :param directory:
    :return:
    """
    if not directory:
        directory = '.'

    venv_directory = os.path.expanduser(os.path.join(directory, name))
    if os.path.exists(venv_directory):
        logger.debug('Removing virtualenv directory %r', venv_directory)
        shutil.rmtree(venv_directory)


def upgrade_package_tools(virtualenv_directory, verbose=False):
    """
    Upgrade the packages used to install/build packages in the virtualenv
    Parameters
    ----------
    virtualenv_directory: str
        The directory that contains the virtualenv
    """
    python_interpreter = os.path.join(virtualenv_directory, 'bin/python')
    pip_command = os.path.join(virtualenv_directory, 'bin/pip')

    for command in [
        [python_interpreter, pip_command, 'install', '--upgrade', 'pip'],
        [python_interpreter, pip_command, 'install', '--upgrade', 'setuptools'],
        [python_interpreter, pip_command, 'install', '--upgrade', 'wheel'],
    ]:
        try:
            output = subprocess.check_output(command, stderr=subprocess.STDOUT)
            if verbose:
                print(output.decode().strip())
        except subprocess.CalledProcessError as error:
            if verbose:
                print(error.output.decode().strip())
            logger.debug(error.output.decode().strip())
            error_message = 'Upgrade command {command} in virtualenv {virtualenv_directory} failed'.format(
                command=command,
                virtualenv_directory=virtualenv_directory
            )
            raise BuildException(error_message)


def build_virtualenv(
        name, directory, python_interpreter=None, user=None, verbose=False):
    """
    Build a virtualenv in a directory

    Parameters
    ----------
    name : str
        Name of the virtualenv to create

    directory : str
        Directory to create the virtualenv in

    python_interpreter : str, optional
        Python interpreter to provide in the virtualenv, defaults to the
        interpreter that is running the virtualenv command

    verbose : bool
        If True, provides status output while running.

    Returns
    -------
    str
        Full path to the root of the virtualenv directory

    Raises
    ------
    BuildException
        The Virtualenv build failed
    """

    # if not python_interpreter:
    #     if not hasattr(sys, 'frozen'):
    #         python_interpreter = sys.executable
    # logger.debug('Python interpreter is: %s' % sys.executable)
    cwd = os.getcwd()
    if not os.path.isdir(directory):
        os.makedirs(directory)

    virtualenv_dir = os.path.join(directory, name)

    user_uid = None
    user_gid = None
    if user:
        user_uid = getpwnam(user).pw_uid
        user_gid = getpwnam(user).pw_gid

    if False and not python_interpreter and BUILTIN_VENV and \
            not hasattr(sys, 'frozen'):
        logger.debug(
            'Building virtualenv %r using the built in venv module',
            virtualenv_dir
        )
        venv.create(virtualenv_dir, with_pip=True)
    else:
        os.chdir(directory)
        command = [virtualenv_command()]
        if python_interpreter:
            command += ['-p', python_interpreter]
        command += [name]
        logger.debug(
            'Building virtualenv using external command %r', ' '.join(command)
        )
        try:
            output = subprocess.check_output(
                command,
                stderr=subprocess.STDOUT,
                # preexec_fn=change_uid_gid(user_uid=user_uid),
            )
            if verbose:
                print(output.decode().strip())
        except subprocess.CalledProcessError as error:
            if verbose:
                print(error.output.decode().strip())
            logger.debug(error.output.decode().strip())
            logger.exception(
                'Virtualenv create command %r failed', ' '.join(command))
            remove_virtualenv(name, directory)
            os.chdir(cwd)
            raise BuildException('Virtualenv create failed')
        os.chdir(cwd)

    for directory_name in ['conf', 'logs']:
        filename = os.path.join(virtualenv_dir, directory_name)
        if not os.path.exists(filename):
            logger.debug('Creating %r directory', filename)
            os.makedirs(filename)

    upgrade_package_tools(virtualenv_dir, verbose=verbose)

    before_binfiles_filename = os.path.join(virtualenv_dir, 'conf/binfiles_predeploy.json')
    with open(before_binfiles_filename, 'w') as before_binfiles_handle:
        before_binfiles = virtualenv_bin_file_hashes(virtualenv_dir)
        before_binfiles_handle.write(json.dumps(before_binfiles))

    return virtualenv_dir


def install_requirements(
        requirements, virtualenv, user=None, upgrade=False, verbose=False,
        pip_version=None, use_index=True
):
    """
    Open one or more requirements files and run pip -r to install them

    Parameters
    ----------
    requirements : str
        Filename containing requirements

    virtualenv : str
        Full path to the virtualenv to install into

    user : str, optional
        The user:group to run the install as

    upgrade : bool
        If True, tell pip to upgrade when running the install.  Default=False

    verbose : bool
        If True, provides status output while running.

    pip_version: str, optional
        Install the requirements with the specified version of pip

    use_index : bool, optional
        Allow pip to use an external index
        Default=True
    """
    logger.info(
        'Installing requirements from requirements file: %r '
        'into virtualenv %r as user %r',
        requirements, virtualenv, user
    )
    logger.debug('Current user is: %r', getpass.getuser())
    logger.debug(
        'Current uid: %d, Effective uid: %d', os.getuid(), os.geteuid()
    )

    if isinstance(requirements, str):
        requirements = [requirements]

    extra_pip_args = []
    root_logger = logging.getLogger()
    if upgrade:
        extra_pip_args.append('-U')
    if not verbose and root_logger.level > logging.DEBUG:
        extra_pip_args.append('-q')

    user_uid = None
    user_gid = None
    if user:
        user_uid = getpwnam(user).pw_uid
        user_gid = getpwnam(user).pw_gid
        logger.debug('Installing pip requirements as %r', user)

    virtualenv_bin = os.path.join(virtualenv, 'bin')
    pip_cache_dir = os.path.join(virtualenv, '.cache')
    pip_cache_dir = '~/.cache'
    if user_uid:
        chown_recursive('pip_cache_dir', user_uid, user_gid)

    for requirement in requirements:
        logger.info('Installing python requirements from file %r', requirement)
        command = [
            os.path.join(virtualenv_bin, 'pip'),
            'install',
            '--cache-dir', pip_cache_dir,
            '-r', requirement,
        ] + extra_pip_args
        logger.debug('Running command: %s', ' '.join(command))
        try:
            output = subprocess.check_output(
                command, stderr=subprocess.STDOUT,
                # preexec_fn=change_uid_gid(user_uid=user_uid)
            )
            if verbose:
                print(output.decode())
        except subprocess.CalledProcessError as error:
            print(error.output.decode())
            logger.exception('PIP install operation failed')
            raise BuildException('PIP install operation failed')

    after_binfiles_filename = os.path.join(
        virtualenv, 'conf/binfiles_postdeploy.json'
    )
    logger.debug('Writing binfiles hashes to %r', after_binfiles_filename)
    with open(after_binfiles_filename, 'w') as after_binfiles_handle:
        after_binfiles = virtualenv_bin_file_hashes(virtualenv)
        after_binfiles_handle.write(json.dumps(after_binfiles))
