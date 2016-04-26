# Copyright (c) 2016, Yahoo Inc.
# Copyrights licensed under the BSD License
# See the accompanying LICENSE.txt file for terms.

"""
Functions for creation of packages with single file executables that don't
require any other dependencies.
"""
import logging
import os


logger = logging.getLogger(__name__)  # pylint: disable=C0103


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
            'pip',
            'pip2',
            'pip3',
            'pip2.7',
            'pip3.4',
            'pip3.5',
            'python-config',
            'python',
            'python2.7',
            'python3',
            'python3.4',
            'python3.5',
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
        #     logger.debug('%r is not a file', filename)
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
