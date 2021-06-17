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
from . import __version__
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

    def __init__(self, config_file='deploy.conf', source_dir=''):
        self._wheel_hashes = {}
        self.config_file = config_file
        self.config = get_configuration_dict(configuration=config_file)
        self.source_dir = source_dir if source_dir else os.getcwd()
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
    def basepython(self):
        """
        Determine the value of basepython for this plugin

        Returns
        -------
        str: basepython
        """
        basepython = self.config['global'].get('basepython', 'python3')

        # If basepython is set in the packages section it needs to override the global default
        for format in self.package_formats:
            pkg_cfg = self.config.get(format + "_package", {})
            if basepython in pkg_cfg.keys():
                print('Using basepython from %s_package section' % format)
                basepython = pkg_cfg['basepython']


        return basepython

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
        python_executable = find_executable(self.basepython)
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

    def copy_files_to_tempdir(self, tempdir):
        """
        Copy any files from the sourcedir into the tempdir for package generation
        """
        pass

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

        use_local_wheels = self.config['global'].get('use_local_wheels', 'false').lower() in ['1', 'true', 'yes', 'on']
        include_hashes = self.config['pip'].get('hash_dependencies', 'false').lower() in ['1', 'true', 'yes', 'on']

        original_directory = os.getcwd()

        with InTemporaryDirectory() as tempdir:
            self.copy_files_to_tempdir(tempdir)

            wheel_dir = 'wheels'
            os.makedirs(wheel_dir)
            hashes = self.generate_wheel_packages(wheel_dir)
            self.generate_wheel_archive()
            deps = []
            for package_name, package_hash in hashes.items():
                if include_hashes:
                    deps.append('{package_name} --hash={package_hash}'.format(package_name=package_name, package_hash=package_hash))
                else:
                    deps.append(package_name)
            self.config['pip']['deps'] = deps
            if self.hash:
                self.loaded_configuration['pip']['deps'] = '\n'.join(deps)
            with open('deploy.conf.unparsed', 'w') as deploy_conf_handle:
                self.loaded_configuration.write(deploy_conf_handle)
            with open('deploy.conf.unparsed') as fh:
                logger.debug('deploy.conf.unparsed %s', fh.read())
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
            deps = self.config['pip'].get('deps', []) + ['invirtualenv', 'configparser']
            cmd = self.pip_cmd + ['wheel', '-w', '.'] + deps
            logger.debug('Running pip command %r to generate wheel packages', cmd)
            try:
                output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()  # nosec
            except subprocess.CalledProcessError as error:
                logger.warning('Exception occurred while generating wheel packages, downloading source packages')
                if error.stdout:
                    logger.error(error.stdout.decode())
                if error.stderr:
                    logger.error(error.stderr.decode())
                cmd = self.pip_cmd + ['download', '-d', '.'] + deps
                logger.debug('Running pip command %r to download missing packages', cmd)
                try:
                    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()  # nosec
                except subprocess.CalledProcessError as error:
                    logger.warning('Exception occurred while downloading source packages')
                    if error.stdout:
                        logger.error(error.stdout.decode())
                    if error.stderr:
                        logger.error(error.stderr.decode())
                    raise
            for filename in os.listdir('.'):
                if filename.endswith('.whl'):
                    split_filename = os.path.basename(filename).split('-')
                    file_wheel_name = filename
                    file_wheel_version = None
                    if len(split_filename) > 2:
                        file_wheel_name = split_filename[0]
                        file_wheel_version = split_filename[1]
                    if self.noarch and not filename.endswith('none-any.whl'):
                        self.noarch = False
                    cmd = self.pip_cmd + ['hash']
                    if self.hash:
                        cmd += ['-a', self.hash]
                    cmd += [filename]
                    logger.debug('Running pip command %r to generate package hash for %r', cmd, filename)
                    hash_result = subprocess.check_output(cmd).decode()  # nosec
                    if file_wheel_name and file_wheel_version:
                        logger.debug("{file_wheel_name}=={file_wheel_version}".format(**locals()))
                        hashes['{file_wheel_name}=={file_wheel_version}'.format(**locals())] = '='.join(hash_result.split(os.linesep)[1].split('=')[1:])
                        logger.debug('Got requirements line %r', hashes['{file_wheel_name}=={file_wheel_version}'.format(**locals())])
                    else:
                        hashes[filename] = '='.join(hash_result.split(os.linesep)[1].split('=')[1:])  # nosec
                        logger.debug('Got requirements line %r', hashes[filename])
        self._wheel_hashes = hashes
        self.add_plugin_configuration()
        return hashes

    def add_plugin_configuration(self):
        """
        Add any specific plugin configuration values to the configuration
        :return:
        """
        pass

    def render_template_with_config(self, template_str=''):

        if not template_str:
            template_str = self.package_template

        original_directory = os.getcwd()

        use_local_wheels = self.config['global'].get('use_local_wheels', 'false').lower() in ['1', 'true', 'yes', 'on']
        include_hashes = self.config['pip'].get('hash_dependencies', 'false').lower() in ['1', 'true', 'yes', 'on']

        with InTemporaryDirectory() as tempdir:
            self.copy_files_to_tempdir(tempdir)
            if self._wheel_hashes:
                hashes = self._wheel_hashes
            else:
                wheel_dir = 'wheels'
                os.makedirs(wheel_dir, exist_ok=True)
                hashes = self.generate_wheel_packages(wheel_dir)

            deps = []
            for package_name, package_hash in hashes.items():
                if use_local_wheels and include_hashes:
                    deps.append('{package_name} --hash={package_hash}'.format(package_name=package_name, package_hash=package_hash))
                else:
                    deps.append(package_name)
            self.config['pip']['deps'] = deps

            if use_local_wheels or include_hashes:
                self.loaded_configuration['pip']['deps'] = '\n'.join(deps)

        template = Template(template_str)
        return template.render(self.config)
