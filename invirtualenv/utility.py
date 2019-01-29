# Copyright (c) 2016, Yahoo Inc.
# Copyrights licensed under the BSD License
# See the accompanying LICENSE.txt file for terms.

"""
General utility functionality module
"""
from __future__ import print_function
import logging
import os
import textwrap
import sys
from jinja2 import Template
from distutils.spawn import find_executable
from .exceptions import CommandNotFound


logger = logging.getLogger(__name__)  # pylint: disable=C0103


def get_terminal_size():
    """
    Get the terminal rows and columns if we are running on an
    interactive terminal.
    Returns
    -------
    rows : int
        The number of rows on the current terminal.
    columns : int
        The number of columns on the current terminal.
    """
    try:
        rows, columns = os.popen('stty size', 'r').read().split()
    except ValueError:  # pragma: no cover
        rows = 24
        columns = 80
    return int(rows), int(columns)


def display_header(
        text='', width=None, separator=None, outfile=None, collapse=False
):
    """
    Display a textual header message.
    Parameters
    ----------
    text : str
        The text to print/display
    width : int, optional
        The width (text wrap) of the header message.
        This will be the current terminal width as determined
        by the 'stty size' shell command if not specified.
    separator : str, optional
        The character or string to use as a horizontal
        separator.  Will use '=' if one is not specified.
    outfile : File, optional
        The File object to print the header text to.
        This will use sys.stdout if not specified.
    :return:
    """
    if not outfile:
        outfile = sys.stdout
    width = width or get_terminal_size()[1]
    separator = separator or '='
    # Screwdriver buffers stdout and stderr separately.  This can
    # cause output from previous operations to show after our
    # header text.  So we flush the output streams to ensure
    # all existing output is sent/displayed before printing our
    # header.
    sys.stderr.flush()
    outfile.flush()

    if collapse:
        for line in textwrap.wrap(text, width=width-4):
            header_line = separator + ' ' + line + ' ' + \
                separator * (width - 4 - len(line))
            print(header_line, file=outfile)
    else:
        # Print the header text
        horiz = separator * width
        print(horiz, file=outfile)
        print(
            os.linesep.join(textwrap.wrap(text, width=width)),
            file=outfile
        )
        print(horiz, file=outfile)

    # Once again flush our header to the output stream so things
    # show up in the correct order.
    sys.stderr.flush()
    outfile.flush()


def which(command):
    """
    Function searches the path for the command executable

    Parameters
    ----------
    command : str

    Returns
    -------
    str
        Path to the command

    Raises
    ------
    CommandNotFound:
        Command was not found
    """
    bin_dir = os.path.dirname(sys.executable)
    bin_exe = os.path.join(bin_dir, command)
    if os.path.exists(bin_exe) and os.access(bin_exe, os.X_OK):  # pragma: no cover
        return bin_exe
    result = find_executable(command)
    if not result:  # pragma: no cover
        raise CommandNotFound('Command %r was not found in the path' % command)
    return result


def csv_list(value):
    """
    Convert a comma separated string into a list

    Parameters
    ----------
    value : str
        The string object to convert to a list

    Returns
    -------
    list
        A list based on splitting the string on the ',' character
    """
    if value:
        result = []
        for item in value.split(','):
            item = item.strip()
            if item:
                result.append(item)
        return result
    return []


def str_to_bool(value):
    """
    Convert a string too a bool object

    Parameters
    ----------
    value : str
        The string object to convert to a bool.  The following case insensitive
        strings evaluate to True ['true', 1', 'up', 'on']

    Returns
    -------
    bool
        Boolean based on the string
    """
    value = value.lower()
    return value in ['true', '1', 'up', 'on']


def str_to_list(value):
    """
    Convert a newline terminated string into a list.  Any empty lines
    will be removed from the result list.

    Parameters
    ----------
    value : str
        The string object to convert to a list

    Returns
    -------
    list
        List based on the string
    """
    result_list = []
    for item in value.strip().split('\n'):
        item = item.strip()
        if item:
            result_list.append(item)

    return result_list


def str_to_dict(value):
    """
    Convert a newline terminated string of key=value into a dictionary.

    Parameters
    ----------
    value : str
        The string object to convert to a dictionary

    Returns
    -------
    dict
        Dictionary based on the string
    """

    result_dict = {}
    for item in str_to_list(value):
        split_setting = item.split('=')
        result_dict[split_setting[0]] = '='.join(split_setting[1:])
    return result_dict


def str_format_env(value):
    """
    Substitute values with environment variables in a string

    Parameters
    ----------
    value : str
        The string object to be formatted and converted into a list

    Returns
    -------
    str
        With env variable values substituded
    """
    template = Template(value)
    result = template.render(**os.environ)
    if result != value:
        logger.debug('Rendered: %r to %r', value, result)
    return result


def change_uid_gid(user_uid=None, user_gid=None):  # pragma: no cover
    """
    preexec_fn to change the uid/gid when using subprocess

    Parameters
    ----------
    user_uid : int, optional
        The user UID to set to, does not set user uid if this is not passed

    user_gid : int, optional
        The user GID to set to, does not set the gid if this is not passed
    """
    if user_uid is not None:
        os.setuid(user_uid)
    if user_gid is not None:
        os.setgid(user_gid)


def chown_recursive(path, uid, gid):  # pragma: no cover
    """
    Change the ownership of all files and directories in path

    Parameters
    ----------
    path : str
        The root path to start changing the ownership at

    uid, : int
        The uid to change the ownership to

    gid, : int
        The gid to change the ownership to
    """
    for root, dirs, files in os.walk(path):
        for item in dirs:
            os.chown(os.path.join(root, item), uid, gid)
        for item in files:
            os.chown(os.path.join(root, item), uid, gid)


def update_recursive_generator(basedict, updatedict):
    """
    Recursively run update on a dictionary

    Parameters
    ----------
    basedict : dict
        First dictionary, which will contain the updated result

    updatedict : dict
        Second dictionary that will be be updated to basedict, conflicts will
        be replaced with the values from this dictionary.

    Returns
    -------
    dict
        basedict updated to contain the values from updatedict

    """
    for key in set(basedict.keys()) | set(updatedict.keys()):
        if key in basedict and key in updatedict:
            # Both dicts have the same key
            if isinstance(basedict[key], dict) and \
                    isinstance(updatedict[key], dict):
                # Both values are  dicts so merge them.
                yield (
                    key,
                    dict(
                        update_recursive_generator(
                            basedict[key],
                            updatedict[key]
                        )
                    )
                )
            else:
                # One of the values isn't a dict to merge so use the value from
                # updatedict.
                yield (key, updatedict[key])
        elif key in basedict:
            yield (key, basedict[key])
        else:
            yield (key, updatedict[key])


def update_recursive(basedict, updatedict):
    """
    Recursively run update on a dictionary

    Parameters
    ----------
    basedict : dict
        First dictionary, which will contain the updated result

    updatedict : dict
        Second dictionary that will be be updated to basedict, conflicts will
        be replaced with the values from this dictionary.

    Returns
    -------
    dict
        basedict updated to contain the values from updatedict

    """
    return dict(update_recursive_generator(basedict, updatedict))
