"""
Command line interface to invirtualenv v2
"""
import argparse
import logging
import os
import sys
from .config import get_configuration_dict
from .contextmanager import InTemporaryDirectory
from .exceptions import PackageGenerationFailure
from .plugin import create_package, create_package_configuration, get_package_plugin, package_formats


LOGGER = logging.getLogger(__name__)


def parse_cli_arguments():

    # Determine the package types we can create on the current system
    package_choices = package_formats()

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--deploy_conf', default='deploy.conf', help='Deploy configuration filename or url')
    command_parser = parser.add_subparsers(title='command', dest='command')
    list_plugins_parser = command_parser.add_parser('list_plugins', help='List the installed invirtualenv plugins')
    package_config_parser = command_parser.add_parser('create_package_config', help='Generate the packaging configuration file')
    package_config_parser.add_argument('package_type', choices=package_choices, help='Type of package to create')
    package_config_parser.add_argument('--outfile', '-o', default=None, help='Output file name')

    package_create_parser = command_parser.add_parser('create_package', help='Generate a package from a deployment configuration')
    package_create_parser.add_argument('package_type', choices=package_choices, help='Type of package to create')

    get_setting_parser = command_parser.add_parser('get_setting', help='Get a setting value from the configuration')
    get_setting_parser.add_argument('section', help="the configuration section to get the setting from")
    get_setting_parser.add_argument('item', help='The item to get from the configuration')
    args = parser.parse_args()
    return args


def get_setting_command(args):
    """
    Get the value of a setting in the deploy.conf

    Parameters
    ----------
    args: argparse.Namespace
        The argparse parser namespace with the parsed cli settings

    Returns
    -------
    str:
        The value of the setting or None
    """
    LOGGER.debug('Getting value for %s=%s', args.section, args.item)
    rc = 0
    config = get_configuration_dict([args.deploy_conf])
    try:
        value = config[args.section][args.item]
    except KeyError:
        value = ''
        rc = 1
    LOGGER.debug('Got value %r for %s=%s', value, args.section, args.item)
    return rc, value


def create_config_command(args):
    if not package_formats():  # pragma: no cover
        raise PackageGenerationFailure('No supported package creation plugins found')

    outfile = args.outfile
    if not outfile:
        plugin = get_package_plugin(args.package_type)
        outfile = plugin.default_config_filename

    deploy_config_contents = ''
    with open(args.deploy_conf) as deploy_conf_handle:
        deploy_config_contents = deploy_conf_handle.read()

    with InTemporaryDirectory():
        with open('deploy.conf', 'w') as deploy_conf_handle:
            deploy_conf_handle.write(deploy_config_contents)

    result = create_package_configuration(args.package_type)
    if outfile:
        with open(outfile, 'w') as output_handle:
            output_handle.write(result)
    else:
        sys.stdout.write(result)

    return 0, outfile


def create_package_command(args):
    if not package_formats():
        raise PackageGenerationFailure('No supported package creation plugins found')

    deploy_config_contents = ''
    with open(args.deploy_conf) as deploy_conf_handle:
        deploy_config_contents = deploy_conf_handle.read()

    orig_directory = os.getcwd()
    with InTemporaryDirectory():
        with open(args.deploy_conf, 'w') as deploy_conf_handle:
            deploy_conf_handle.write(deploy_config_contents)
        package_file = create_package(args.package_type)
        dest_package_file = os.path.join(orig_directory, os.path.basename(package_file))
        if os.path.exists(package_file):
            os.rename(package_file, dest_package_file)

    if package_file:
        logging.debug('Generated package file: %s' % dest_package_file)
        return 0, 'Generated package file:' + dest_package_file

    raise PackageGenerationFailure('Unable to generate a package file using the %r plugin' % args.package_type)


def list_plugins_command(args):
    installed_plugins = package_formats()

    if not installed_plugins:
        return 0, 'No plugins are installed'
    result = 'Installed plugins:' + os.linesep
    for plugin in package_formats():
        result += '\t' + plugin + os.linesep
    return 0, result


def main(test=False):
    logging.basicConfig(level=logging.INFO)
    args = parse_cli_arguments()

    rc = 0
    output = ''
    if args.command in ['create_package']:
        rc, output = create_package_command(args)
    elif args.command in ['create_package_config']:
        rc, output = create_config_command(args)
    elif args.command in ['list_plugins']:
        rc, output = list_plugins_command(args)
    elif args.command in ['get_setting']:
        rc, output = get_setting_command(args)
    if test:
        return rc, output

    print(output)
    sys.exit(rc)
