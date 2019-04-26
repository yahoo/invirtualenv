# Copyright (c) 2016, Yahoo Inc.
# Copyrights licensed under the BSD License
# See the accompanying LICENSE.txt file for terms.
"""
Useful contextmanagers
"""
from __future__ import print_function
from contextlib import contextmanager
import errno
import logging
import os
import shutil
import tempfile


LOG = logging.getLogger(__name__)


@contextmanager
def working_dir(new_path):
    """
    A context manager that changes to the new_path directory and
    returns to the current working directory when it completes.
    """
    old_dir = os.getcwd()
    os.chdir(new_path)
    try:
        yield
    finally:
        os.chdir(old_dir)


@contextmanager
def revert_file(filename):
    """
    A context manager that reverts a file's contents.
    """
    original_data = None
    with open(filename, 'rb') as file_handle:
        original_data = file_handle.read()

    try:
        yield
    finally:
        if original_data:  # pragma: no cover
            with open(filename, 'wb') as file_handle:
                file_handle.write(original_data)


@contextmanager
def TemporaryDirectory():  # pylint: disable=C0103
    """
    A context manager that provides a temporary directory and cleans it up.

    Note:
        This context manager duplicates the base functionality of the
        tempfile.TemporaryDirectory() context manager in Python 3.2+

    Returns
    -------
    str
        The path to the temporary directory
    """
    name = tempfile.mkdtemp()
    try:
        yield name
    finally:
        try:
            shutil.rmtree(name)
        except OSError as error:  # pragma: no cover
            # Reraise unless ENOENT: No such file or directory
            # (ok if directory has already been deleted)
            if error.errno != errno.ENOENT:
                raise


@contextmanager
def InTemporaryDirectory():  # pylint: disable=C0103
    """
    A context manager that creates a temporary directory and changes
    the current directory into it.
    """
    with TemporaryDirectory() as tempdir:
        with working_dir(tempdir):
            yield
