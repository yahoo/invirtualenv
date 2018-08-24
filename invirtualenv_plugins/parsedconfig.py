import logging
import os
from invirtualenv.config import generate_parsed_config_file
from invirtualenv.plugin_base import InvirtualenvPlugin


logger = logging.getLogger(__name__)


class InvirtualenvParsedConfig(InvirtualenvPlugin):
    package_formats = ['parsed_deploy_conf']
    default_config_filename = 'deploy.conf.parsed'

    def __init__(self, *args, **kwargs):
        super(InvirtualenvParsedConfig, self).__init__(*args, **kwargs)
        if not os.path.exists(self.config_file):
            raise FileNotFoundError('Configuration file %r was not found' % self.config_file)

        with open(self.config_file) as config_file_handle:
            self.package_template = config_file_handle.read()
        logger.debug('Read template %r', self.package_template)

    def run_package_command(self, package_hashes, wheel_dir='wheels'):
        logger.debug('Config')
        logger.debug(self.config)
        logger.debug('Deploy.conf')
        logger.debug(open('deploy.conf').read())
        generate_parsed_config_file('deploy.conf', self.default_config_filename)
        return self.default_config_filename

