# Copyright (c) 2016, Yahoo Inc.
# Copyrights licensed under the BSD License
# See the accompanying LICENSE.txt file for terms.

"""
Module to create/deploy a virtualenv
"""
from __future__ import print_function
import getpass
import json
import logging
import os
from pwd import getpwnam
import subprocess
import tempfile
from .utility import display_header
from .config import get_configuration_dict, parse_arguments
from .exceptions import AlreadyExists, BuildException, \
    InsufficientPermissions, NoPackageVersions
from .package import install_prereq_packages, latest_package_version
from .utility import which
from .virtualenv import build_virtualenv, install_requirements, \
    remove_virtualenv


logger = logging.getLogger(__name__)  # pylint: disable=C0103


COMMANDS = {
    'apt-get': '/usr/bin/apt-get',
    'pip': 'pip',
    'yum': '/usr/bin/yum'
}


def fix_file_ownership(virtualenv, user, group):
    """
    Fix the file ownership of a virtualenv

    Parameters
    ----------
    virtualenv : str
        Virtualenv path

    user : str
        User to change to

    group : str
        Group to change to
    :return:
    """
    if (user and group) and virtualenv:
        subprocess.check_call(
            [
                'chown',
                '-R',
                '%s:%s' % (
                    user,
                    group
                ),
                virtualenv
            ]
        )
        subprocess.check_call(
            ['chmod', '-R', 'g+wx', virtualenv]
        )


def install_python_dependencies(virtualenv, deps=None, requirements=None, upgrade=False, verbose=False, pip_version=None, use_index=True):
    """
    Install python dependencies from a requirements file or
    deploy.conf manifest

    Parameters
    ----------
    virtualenv : str
        The virtualenv to install into

    deps : list, optional
        A list of python packages to install

    requirements : str, optional
        The requirements.txt file to install from

    upgrade : bool, optional
        Tell pip to upgrade packages when installing, Default=False

    verbose : bool, optional
        Display command output when running the dependency operations,
        Default=False

    use_index : bool, optional
        Allow pip to use an external index
        Default=True

    Raises
    ------
    BuildException - If package installation fails
    """
    if not deps and not requirements:  # pragma: no cover
        if verbose:
            print('No requirements specified to install')
        return

    if deps:
        logger.debug('Installing dependencies from configuration deps: %s', ' '.join(deps))
        with tempfile.NamedTemporaryFile() as requirements_handle:
            requirements_handle.write('\n'.join(deps).encode())
            requirements_handle.flush()
            requirements_handle.seek(0)
            install_requirements(
                requirements_handle.name,
                virtualenv=virtualenv,
                upgrade=upgrade,
                verbose=verbose,
                pip_version=pip_version,
                use_index=use_index
            )
    if requirements:
        logger.debug('Installing dependencies from requirements file %r', requirements)
        install_requirements(
            requirements, virtualenv=virtualenv, upgrade=upgrade,
            verbose=verbose, pip_version=pip_version, use_index=use_index
        )


def install_rpm_dependencies(deps=None, fail_missing=True):  # pragma: no cover
    """
    Install rpm dependencies from deploy.conf manifest

    Parameters
    ----------
    deps : list, optional
        A list of rpm packages to install

    fail_missing : bool, optional
        Generate an exception and fail if the "yum" command is not available.
        default = True

    Raises
    ------
    BuildException - If package installation fails
    """
    if deps and not os.path.exists(COMMANDS['yum']):
        if fail_missing:
            raise BuildException('No %r command available' % COMMANDS['yum'])
        logger.warning('The %r command is missing', COMMANDS['yum'])

    if deps:
        logger.debug('Installing yum packages: %r', deps)
        if os.path.exists(COMMANDS['yum']):
            command = [COMMANDS['yum'], 'install', '-y'] + deps
            logger.debug('Running command: %s', ' '.join(command))
            subprocess.check_call(command)


def build_deploy_virtualenv(arguments=None, configuration=None, update_existing=True, verbose=None):
    """
    Build and deploy a python virtualenv

    Parameters
    ----------
    arguments : argparse namespace, optional
        An argparse namespace with all of the required command line arguments
        defaults to parsing the command line arguments if not provided.

    configuration : str or list, optional
        A configuration file or list of configuration files to parse,
        defaults to the deploy_default.conf file in the package and
        deploy.conf in the current working directory.

    update_existing : bool
        If True, allow updating an existing virtualenv, Otherwise generate
        an exception.  Default=True

    verbose : bool
        If True, provides status output while running.

    Raises
    ------
    AlreadyExists
        The virtualenv already exists

    BuildError
        The specified package manifest cannot be deployed to the virtualenv

    InsufficientPermissions
        The current user lacks permissions to complete the specified operation

    NoPackageVersions
        A virtualenv_version_package was specified in the configuration but
        no versions for that package where found on artifactory.
    """
    # display_header('Parsing the configuration')
    config = get_configuration_dict(configuration=configuration)
    if not arguments:
        logger.debug(
            'No arguments dictionary passed, parsing command line arguments')
        arguments = parse_arguments(configuration=configuration)
        logger.debug('Arguments are: %s', arguments)

    if verbose is None:
        verbose = arguments.verbose

    # If an interperter is specified, validate it exists
    if config['global']['basepython']:
        if not os.path.exists(config['global']['basepython']):
            config['global']['basepython'] = which(
                config['global']['basepython'])

    version = config['global']['version']
    if arguments.virtualenvversion_package:
        if verbose:
            display_header(
                'Getting version based on package %r from artifactory' %
                arguments.virtualenvversion_package
            )
        version = latest_package_version(arguments.virtualenvversion_package)
        if not version:
            raise NoPackageVersions(
                'Unable to find any package versions on for package '
                '%r' % arguments.virtualenvversion_package
            )

    if version:
        arguments.name += '_' + version

    logger.debug('Using version: ' + version)

    # In no package manifest installs where specified default to all
    if not config['global']['install_manifest']:
        config['global']['install_manifest'] = ['pip', 'rpm']

    # Make sure we have needed privileges
    if os.geteuid() != 0:
        if 'rpm' in config['global']['install_manifest']:
            if config['rpm']['deps']:
                raise InsufficientPermissions(
                    'Must run as root to install rpm packages'
                )
        if arguments.install_os_packages:
            raise InsufficientPermissions(
                'Must run as root to install python pre-req rpm packages'
            )

    # Make sure we aren't overwriting a virtualenv without specifying
    # update.
    virtualenv = os.path.join(arguments.virtualenvdir, arguments.name)
    if os.path.exists(virtualenv):
        if not update_existing:
            raise AlreadyExists(
                'Virtualenv %r already exists' % virtualenv
            )

    # Install the python OS rpm packages if requested.
    if arguments.install_os_packages:
        if verbose:
            display_header('Installing Operating System Pre-Req packages')
        install_prereq_packages()

    # Install rpm packages if specified
    if 'rpm' in config['global']['install_manifest']:
        if config['rpm']['deps']:
            if verbose:
                display_header('Installing rpm dependencies')
            install_rpm_dependencies(
                deps=config['rpm']['deps'],
                fail_missing=config['rpm']['fail_missing_yum']
            )

    if verbose:
        display_header('Building virtualenv')
    virtualenv = build_virtualenv(
        arguments.name,
        arguments.virtualenvdir,
        python_interpreter=arguments.python,
        user=arguments.virtualenvuser,
        verbose=verbose
    )

    deps = config['pip']['deps']
    use_index = True
    if verbose:
        display_header('Installing python package dependencies')
    try:
        install_python_dependencies(
            virtualenv=virtualenv,
            requirements=arguments.requirement,
            deps=config['pip']['deps'],
            upgrade=arguments.upgrade,
            verbose=verbose,
            pip_version=config['pip']['pip_version'],
            use_index=use_index
        )
    except BuildException:
        logger.exception(
            'Package installation in virtualenv failed, removing virtualenv',
        )
        remove_virtualenv(arguments.name, arguments.virtualenvdir)
        raise BuildException('Package installation in virtualenv failed')

    if not arguments.virtualenvuser and not arguments.virtualenvgroup:
        # User didn't specify a user or group
        return

    # Fixing ownership requires both user and group so make sure both
    # are populated if the user didn't pass them.
    if not arguments.virtualenvuser:
        arguments.virtualenvuser = getpass.getuser()

    if not arguments.virtualenvgroup:
        arguments.virtualenvgroup = getpwnam(arguments.virtualenvuser).pw_gid

    if verbose:
        display_header('Fixing file ownership')
    fix_file_ownership(virtualenv, arguments.virtualenvuser, arguments.virtualenvgroup)

    return virtualenv


def deployed_bin_files(venv):
    """
    Gets files that where deployed to the bin directory of the virtualenv.

    Parameters
    ----------
    venv : str
        Path the to virtualenv to do this bin_file links for

    Returns
    -------
    dict
        Key = filename
        Value = sha256 hash
    """
    linked_files = []
    confdir = os.path.join(venv, 'conf')
    before_files_conf = os.path.join(confdir, 'binfiles_predeploy.json')
    after_files_conf = os.path.join(confdir, 'binfiles_postdeploy.json')
    if not os.path.exists(before_files_conf):
        logger.debug('No binfiles_predeploy.json is present')
        return linked_files
    if not os.path.exists(after_files_conf):
        logger.debug('No binfiles_postdeploy.json is present')
        return linked_files

    with open(before_files_conf) as handle:
        before_files = json.load(handle)
    with open(after_files_conf) as handle:
        after_files = json.load(handle)

    before = set(before_files.keys())
    after = set(after_files.keys())

    deployed_files = list(after.difference(before))
    result = {}
    for filename in deployed_files:
        result[filename] = after_files[filename]
    return result


def link_deployed_bin_files(venv, destbin):  # pragma: no cover
    """
    Link the deployed files from the venv bin directory into the destbin
    directory.

    Writes a json list of the created links to conf/created_links.json in
    the virtualenv.

    Parameters
    ----------
    venv: str
        Path to the python virtualenv

    destbin: str
        Destination directory when the links should be

    Returns
    -------
    list
        Full path to files linked
    """
    linked_files = []
    venv_bin = os.path.join(venv, 'bin')
    venv_conf = os.path.join(venv, 'conf')
    linked_files_conf = os.path.join(venv_conf, 'created_links.json')
    for filename in deployed_bin_files(venv):
        source_filename = os.path.expanduser(os.path.join(venv_bin, filename))
        dest_filename = os.path.expanduser(os.path.join(destbin, filename))
        if os.path.exists(dest_filename):
            logger.debug('Not overwriting existing file %r', dest_filename)
            continue

        # os.path.exists() returns False for broken symlinks so we need to check
        # to see if the dest_filename is a symlink.
        if os.path.islink(dest_filename):
            logger.warning('Removing broken symlink %r', dest_filename)
            os.unlink(dest_filename)
        os.symlink(source_filename, dest_filename)
        linked_files.append(dest_filename)
    with open(linked_files_conf, 'w') as handle:
        json.dump(linked_files, handle)


def unlink_deployed_bin_files(venv):  # pragma: no cover
    """
    Undo/delete the symlinks created by link_deployed_bin_files()

    Parameters
    ----------
    venv:str
        Path to the root of the virtualenv
    """
    venv_conf = os.path.join(venv, 'conf')
    linked_files_conf = os.path.join(venv_conf, 'created_links.json')
    if not os.path.exists(linked_files_conf):
        logger.debug('No symlinked files for this virtualenv')
        return
    with open(linked_files_conf, 'r') as handle:
        for filename in json.load(handle):
            if os.path.islink(filename):
                logger.debug('Removing symlink %r', filename)
                os.remove(filename)
                continue
            if os.path.exists(filename):
                logger.debug('File %r is not a symlink, not removing', filename)
                continue
            logger.debug('File %r is missing, cannot remove symlink', filename)
    os.remove(linked_files_conf)
