"""
Command line interface to invirtualenv
"""
import argparse
import logging
import os
import sys
from .contextmanager import InTemporaryDirectory
from .exceptions import PackageGenerationFailure
from .plugin import create_package, create_package_configuration, package_formats


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
    package_config_parser.add_argument('--outfile', '-o', default=None, help='Type of package to create')

    package_create_parser = command_parser.add_parser('create_package', help='Generate a package from a deployment configuration')
    package_create_parser.add_argument('package_type', choices=package_choices, help='Type of package to create')

    args = parser.parse_args()
    return args


def create_config_command(args):
    if not package_formats():
        raise PackageGenerationFailure('No supported package creation plugins found')

    deploy_config_contents = ''
    with open(args.deploy_conf) as deploy_conf_handle:
        deploy_config_contents = deploy_conf_handle.read()

    destdir = os.getcwd()
    with InTemporaryDirectory():
        with open('deploy.conf', 'w') as deploy_conf_handle:
            deploy_conf_handle.write(deploy_config_contents)

    result = create_package_configuration(args.package_type)
    if args.outfile:
        with open(args.outfile, 'w') as output_handle:
            output_handle.write(result)
    return 0, args.outfile


def create_package_command(args):
    if not package_formats():
        raise PackageGenerationFailure('No supported package creation plugins found')

    deploy_config_contents = ''
    with open(args.deploy_conf) as deploy_conf_handle:
        deploy_config_contents = deploy_conf_handle.read()

    destdir = os.getcwd()
    with InTemporaryDirectory():
        with open('deploy.conf', 'w') as deploy_conf_handle:
            deploy_conf_handle.write(deploy_config_contents)
        package_file = create_package(args.package_type)
        if os.path.exists(package_file):
            os.rename(package_file, os.path.join(destdir, package_file))

    if package_file:
        logging.debug('Generated package file: %s' % package_file)
        return 0, 'Generated package file:' + package_file

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
    # logging.basicConfig(level=logging.DEBUG)
    args = parse_cli_arguments()

    rc = 0
    output = ''
    if args.command in ['create_package']:
        rc, output = create_package_command(args)
    elif args.command in ['create_package_config']:
        rc, output = create_config_command(args)
    elif args.command in ['list_plugins']:
        rc, output = list_plugins_command(args)

    if test:
        return rc, output

    print(output)
    sys.exit(rc)
