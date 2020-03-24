# Copyright (c) 2016, Yahoo Inc.
# Copyrights licensed under the BSD License
# See the accompanying LICENSE.txt file for terms.

"""
Functions to enable packaging plugin functionality
"""
import logging
import os
import shutil
import subprocess  # nosec
import sys
from jinja2 import Template
from .config import get_configuration_dict, get_configuration, generate_parsed_config_file
from .contextmanager import InTemporaryDirectory, working_dir
from .utility import find_executable, update_recursive, csv_list


logger = logging.getLogger(__name__)  # pylint: disable=C0103


class InvirtualenvPlugin(object):
    package_formats = []
    config_default = ""
    config_types = {}
    default_config_filename = 'invirtualenv.configuration'
    package_template = ''
    hash = None  # PIP hash algorithm to use, can be sha256, sha384, sha512 or None (no hashing)
    noarch = True

    def __init__(self, config_file='deploy.conf'):
        self.config_file = config_file
        self.config = get_configuration_dict(configuration=config_file)
        self.loaded_configuration = get_configuration(configuration=config_file)
        self.add_plugin_configuration()

    # Methods that need to be written for each plugin type
    def run_package_command(self, package_hashes, wheel_dir='wheels'):
        """
        Run the command to generate the package based on the hash
        """
        pass

    def system_requirements_ok(self):
        """
        Check if all the system requirements for this plugin are met.

        Returns
        -------
        bool
            True if requirements are met, False otherwise
        """
        return True

    @property
    def pip_cmd(self):
        """
        Get the pip command used to create wheels of packages.

        The intention is to use the same version of pip to build the wheels
        as would be used to deploy them.

        The full path to the python interpreter is used to avoid shebang
        line length issues.

        Returns
        -------
        list
            Command that can be used to invoke pip
        """
        basepython = self.config['global'].get('basepython', 'python3')
        python_executable = find_executable(basepython)
        if not python_executable:
            python_executable = sys.executable
        bin_dir = os.path.dirname(python_executable)
        try:
            output = subprocess.check_output([python_executable, '-m', 'pip'])  # nosec
            return [python_executable, '-m', 'pip']
        except subprocess.CalledProcessError:
            # Try to work around broken pip module
            pip_exe = os.path.join(bin_dir, 'pip3')
            if os.path.exists(pip_exe):
                return [pip_exe]
            return [os.path.join(bin_dir, 'pip')]

    def supported_formats(self):
        """
        Formats supported by this plugin that can be generated on this system

        Returns
        -------
        list
            Package formats that this plugin supports
        """
        if self.system_requirements_ok():
            return self.package_formats
        return []

    def create_package(self, package_type):
        """
        Generate a package of the specified type

        Parameters
        ----------
        str: package_type
            The type of package to generate
        """
        if package_type not in self.supported_formats():
            return None

        original_directory = os.getcwd()
        with InTemporaryDirectory():
            tempdir = os.getcwd()

            wheel_dir = 'wheels'
            os.makedirs(wheel_dir)
            hashes = self.generate_wheel_packages(wheel_dir)
            self.generate_wheel_archive()
            deps = []
            for package_name, package_hash in hashes.items():
                deps.append('{package_name} --hash={package_hash}'.format(package_name=package_name, package_hash=package_hash))
            self.config['pip']['deps'] = deps
            if self.hash:
                self.loaded_configuration['pip']['deps'] = '\n'.join(deps)
            with open('deploy.conf.unparsed', 'w') as deploy_conf_handle:
                self.loaded_configuration.write(deploy_conf_handle)
            generate_parsed_config_file('deploy.conf.unparsed', 'deploy.conf')
            package = self.run_package_command(hashes, wheel_dir=wheel_dir)  # pylint: disable=E1128,E1111
            if package and os.path.exists(package):
                source = package
                dest = os.path.join(original_directory, os.path.basename(package))
                shutil.copyfile(source, dest)
                return dest
            return package

    def generate_wheel_archive(self, filename=None):
        if not filename:
            filename = 'wheels.tar.gz'
        subprocess.check_call(['tar', '-czf', filename, 'wheels'])  # nosec

    def generate_wheel_packages(self, wheeldir):
        """
        Generate wheel packages for all dependencies

        Parameters
        ----------
        wheeldir: str
            The directory path to store the generated wheel packages

        Returns
        -------
        dict of filename, pip requirements line
        """
        if not self.config['pip'].get('deps'):
            return {}
        hashes = {}
        with working_dir(wheeldir):
            logger.debug('Making sure the wheel package is installed')
            subprocess.check_call(self.pip_cmd + ['install', '-U', 'pip'])  # nosec
            subprocess.check_call(self.pip_cmd + ['install', 'wheel'])  # nosec
            deps = self.config['pip'].get('deps', []) + ['invirtualenv']
            cmd = self.pip_cmd + ['wheel', '-w', '.'] + deps
            logger.debug('Running pip command %r to generate wheel packages', cmd)
            subprocess.check_call(cmd)  # nosec
            for filename in os.listdir('.'):
                if filename.endswith('.whl'):
                    if not filename.endswith('none-any.whl'):
                        self.noarch = False
                    cmd = self.pip_cmd + ['hash']
                    if self.hash:
                        cmd += ['-a', self.hash]
                    cmd += [filename]
                    logger.debug('Running pip command %r to generate package hash for %r', cmd, filename)
                    hashes[filename] = '='.join(subprocess.check_output(cmd).decode().split(os.linesep)[1].split('=')[1:])  # nosec
                    logger.debug('Got requirements line %r', hashes[filename])
        return hashes

    def add_plugin_configuration(self):
        """
        Add any specific plugin configuration values to the configuration
        :return:
        """
        pass

    def render_template_with_config(self, template_str=None):
        if not template_str:
            template_str = self.package_template
            template = Template(template_str)
            return template.render(self.config)
