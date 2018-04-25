# Copyright (c) 2016, Yahoo Inc.
# Copyrights licensed under the BSD License
# See the accompanying LICENSE.txt file for terms.

"""
Functions for handling the configuration settings
"""
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
import getpass
import io
import logging
import os
import tempfile
# noinspection PyUnresolvedReferences,PyPackageRequirements
from six.moves.configparser import ConfigParser
from jinja2 import Template

from .package import package_scripts_directory
from .plugin import config_defaults, config_types, config_update
from .utility import str_to_bool, str_to_list, str_format_env
from .virtualenv import default_virtualenv_directory


logger = logging.getLogger(__name__)  # pylint: disable=C0103


# Config file that is part of the package
PACKAGE_DEFAULT_CONFIG = os.path.join(
    os.path.dirname(__file__), 'deploy_default.conf'
)

CONFIG_PATH = [
    PACKAGE_DEFAULT_CONFIG,

    # Any deploy.conf files in the current directory
    'deploy.conf'
]


def cast_types(configuration, types_dict=None):
    """
    Update in place the configuration dictionary with inferred values if they
    aren't specified.

    Parameters
    ----------
    configuration : dict
    config_types : dict, optional
        Types dictionary, defaults to value from config_types()
    """
    if not types_dict:
        types_dict = config_types()

    for section, settings in configuration.items():
        for key, value in settings.items():
            try:
                setting_type = types_dict[section][key]
                if setting_type is bool:
                    setting_type = str_to_bool
                elif setting_type is list:
                    setting_type = str_to_list
                configuration[section][key] = setting_type(value)
                logger.debug(
                    'Forced value %r of type %r to type %r, result is %r',
                    value, type(value), setting_type,
                    configuration[section][key]
                )
            except (KeyError, TypeError):
                pass


def get_configuration(configuration=None):
    """
    Parse a configuration file

    Parameters
    ----------
    configuration : str or list, optional
        A configuration file or list of configuration files to parse,
        defaults to the deploy_default.conf file in the package and
        deploy.conf in the current working directory.

    Returns
    -------
    configparser
        The parsed configuration
    """
    if not configuration:  # pragma: no cover
        configuration = [
            # Config file that is part of the package
            # PACKAGE_DEFAULT_CONFIG,

            # Any deploy.conf files in the current directory
            'deploy.conf'
        ]
    config = ConfigParser()

    # Set the config defaults
    try:
        config.read_string(config_defaults())
    except AttributeError:
        config.readfp(io.BytesIO(config_defaults()))

    logger.debug('Working with default dict: %r', config_defaults())
    config.read(configuration)
    return config


def get_configuration_dict(configuration=None, value_types=None):
    """
    Parse the configuration files

    Parameters
    ----------
    configuration : str or list, optional
        A configuration file or list of configuration files to parse,
        defaults to the deploy_default.conf file in the package and
        deploy.conf in the current working directory.

    value_types : dict, optional
        Dictionary containing classes to apply to specific items

    Returns
    -------
    dict
        Configuration dictionary
    """
    if not value_types:  # pragma: no cover
        value_types = config_types()

    config = get_configuration(configuration)

    result_dict = {}
    for section in config.sections():
        result_dict[section] = {}
        for key, val in config.items(section):
            result_dict[section][key] = str_format_env(val)

    config_update(result_dict)

    if 'locations' not in result_dict.keys():
        result_dict['locations'] = {}
    result_dict['locations']['package_scripts'] = package_scripts_directory()
    if not result_dict['global'].get('virtualenv_dir', None):
        result_dict['global']['virtualenv_dir'] = \
            default_virtualenv_directory()

    cast_types(result_dict)

    return result_dict


def generate_parsed_config_file(source=None, dest=None):
    """
    Generate a conf file with the environment variables expanded

    Parameters
    ----------
    source : str, optional
        The path to the source file

    dest : str, optional
        The path to the desired destination file

    Returns
    -------
    str
        Path to the generated config file
    """
    config_data = None
    if not source:  # pragma: no cover
        source = 'deploy.conf'

    if isinstance(source, list):
        source = source[0]

    with open(source) as config_data_handle:
        config_data = config_data_handle.read()

    if not config_data:  # pragma: no cover
        return None

    template = Template(config_data)
    result = template.render(**os.environ)

    if not dest:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix='.conf'
        ) as dest_handle:
            dest_handle.write(result.encode())
            dest = dest_handle.name
    else:
        with open(dest, 'w') as new_conf_handle:
            new_conf_handle.write(result)

    return dest


def parse_arguments(configuration=None):
    """
    Parse the command line arguments

    Parameters
    ----------
    configuration : list, optional
        A list of config files to parse, defaults to the packaged
        deploy_default.conf and the deploy.conf file in the current
        directory.

    Returns
    -------
    argparse namespace object
        With the configuration based on the passed command line arguments
        and defaults from the deploy_default.conf file in the package.
    """
    config = get_configuration_dict(
        configuration,
        config_types()
    )
    virtualenvuser = config['global']['virtualenv_user']
    if not virtualenvuser:  # pragma: no cover
        virtualenvuser = getpass.getuser()

    parser = ArgumentParser(
        description='Deploy a python application into a virtualenv',
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        'name', nargs='?', default=config['global']['name'],
        help='VirtualEnv name'
    )
    parser.add_argument(
        '--python',
        '-p',
        default=config['global']['basepython'],
        help='The Python interpreter to use, e.g., --python=python3.5 '
             'will use the python3.5 interpreter to create the new '
             'environment.  The default is the interpreter that virtualenv '
             'was installed with.'
    )
    parser.add_argument(
        '--requirement',
        '-r',
        default=[],
        action='append',
        help='Install from the given requirements file. This option can be '
             'used multiple times.'
    )
    parser.add_argument(
        '--virtualenvdir',
        default=config['global']['virtualenv_dir'],
        help='Directory to build the virtualenv'
    )
    parser.add_argument(
        '--virtualenvuser',
        default=virtualenvuser,
        help='The user to create the virtualenv'
    )
    parser.add_argument(
        '--virtualenvgroup',
        default=config['global']['virtualenv_group'],
        help='The group to create the virtualenv'
    )
    parser.add_argument(
        '--virtualenvversion_package',
        default=config['global']['virtualenv_version_package'],
        help='Version the virtualenv based on the version of a package'
    )
    parser.add_argument(
        '--install_os_packages',
        default=config['global']['install_os_packages'],
        help='Install OS packages'
    )
    parser.add_argument(
        '--verbose', action='store_true', default=False,
        help='More verbose output'
    )
    parser.add_argument(
        '--upgrade', action='store_true', default=False,
        help='Upgrade packages when installing'
    )
    return parser.parse_args()
