"""
Functions for creation of packages with single file executables that don't
require any other dependencies.
"""
import logging
import os
import shutil
import subprocess
from .deploy import build_deploy_virtualenv


logger = logging.getLogger(__name__)


def python_scripts_in_venv_bin(virtualenv_dir, remove_bins=None):
    """
    Find python scripts in a virtualenv bin directory

    Parameters
    ----------
    virtualenv_dir : str
        The virtualenv directory

    remove_bins : list, optional
        Binary filenames to remove from the list

    Returns
    -------
    list
        The python scripts found in the virtualenv directory
    """
    if not remove_bins:
        remove_bins = [
            'easy_install',
            'easy_install-2.7',
            'easy_install-3.4',
            'easy_install-3.5',
            'easy_install-3.6',
            'pip',
            'pip2',
            'pip3',
            'pip2.7',
            'pip3.4',
            'pip3.5',
            'pip3.6',
            'python-config',
            'python',
            'python2.7',
            'python3',
            'python3.4',
            'python3.5',
            'python3.6',
            'wheel'
        ]

    bin_dir = os.path.join(virtualenv_dir, 'bin')
    bin_python = os.path.join(bin_dir, 'python')

    result_list = []
    logger.info('Scanning bin directory %r for files', bin_dir)
    for item in os.listdir(bin_dir):
        if item in remove_bins:
            logger.debug('Not adding platform binary %r', item)
            continue
        filename = os.path.join(
            bin_dir,
            item
        )
        # if not os.path.isfile(filename):
        #     LOG.debug('%r is not a file', filename)
        #     continue
        with open(filename) as file_handle:
            line1 = file_handle.readline()
            if isinstance(line1, bytes):
                line1 = line1.decode('ascii', 'ignore')
            if not line1.startswith('#!'):
                logger.debug(
                    'First line of the file is not a hashbang')
                continue
            if bin_python not in line1:
                logger.debug(
                    'hashbang line %r does not contain the venv python '
                    'interpreter %r', line1, bin_python)
                continue
            result_list.append(filename)
    return result_list


def create_package(config_file=None, format=None):
    """
    Create a package that contains single file executables of all of the
    package scripts.

    Parameters
    ----------
    config_file : str, optional
        The name of the configuration file to use

    format : str, optional
        The type of package to create, must be one of: ['tar.gz', 'yinst']

    Raises
    ------
    PackageConfigFailure
        The yicf file generation based on the configuration failed

    PackageGenerationFailure
        An error occurred while generating the package

    Returns
    -------
    str
        Filename of the package created
    """
    # Deploy to a virtualenv
    venv_dir = build_deploy_virtualenv(update_existing=False)

    # Generate a list of python executables in the bin directory that were
    # installed by packages.

    # Run 'pyinstaller --onefile {package}' on each script.
    #    command = ['pyinstaller', '--onefile', filename]
    #    LOG.debug('Running command: %r', ' '.join(command))
    #    subprocess.check_call()

    # Package up the executables

    # Cleanup
    shutil.rmtree(venv_dir)
