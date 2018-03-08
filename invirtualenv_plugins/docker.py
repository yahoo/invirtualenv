import logging
import os
import subprocess
from jinja2 import Template
import pkg_resources
import shutil

from invirtualenv.plugin_base import InvirtualenvPlugin
from invirtualenv.utility import csv_list, str_to_dict, find_executable


logger = logging.getLogger(__name__)


DOCKERFILE_TEMPLATE = """FROM {{docker_container['base_image']|default('ubuntu:17.10')}}

{% if docker_container['setenv'] %}# Environment Settings
{% for setting, value in docker_container['setenv'].items() %}ENV {{setting}} {{value}}
{% endfor %}{% endif %}{% if docker_container['files'] %}
# Files
{% for file_line in docker_container['files'] %}COPY {{file_line}}
{% endfor %}{% endif %}{% if docker_container['expose'] %}EXPOSE {{docker_container['expose']}}
{% endif %}# Set up the container
ENV PATH="/var/lib/invirtualvenv/bin:${PATH}"
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y python3-venv python3-dev python3-pip python-virtualenv
RUN mkdir -p /var/lib/virtualenv
RUN mkdir -p /var/lib/invirtualenv/{{global['name']}}
RUN python3.6 -m venv /var/lib/invirtualenv/installervenv
RUN /var/lib/invirtualenv/installervenv/bin/pip install -U setuptools
RUN /var/lib/invirtualenv/installervenv/bin/pip install -U pip wheel virtualenv
RUN /var/lib/invirtualenv/installervenv/bin/pip install invirtualenv
RUN (cd /var/lib/invirtualenv/{{global['name']}} && /var/lib/invirtualenv/installervenv/bin/deploy_virtualenv)
{% if docker_container['entrypoint'] %}ENTRYPOINT {{docker_container['entrypoint']}}
{% endif %}
"""

DOCKER_CONFIG_DEFAULT = """[docker_container]
base_image=ubuntu:17.10
container_name=
entrypoint=/bin/bash
expose:
deb_deps:
files:
rpm_deps:
setenv:
    DEBIAN_FRONTEND=noninteractive
"""


class InvirtualenvDocker(InvirtualenvPlugin):
    package_formats = ['docker']
    package_template = DOCKERFILE_TEMPLATE
    config_default = DOCKER_CONFIG_DEFAULT
    config_types = {
        'docker_container': {
            'base_image': str,
            'container_name': str,
            'deb_deps': list,
            'entrypoint': str,
            'expose': csv_list,
            'files': list,
            'rpm_deps': list,
            'setenv': str_to_dict,
        }
    }

    def system_requirements_ok(self):
        if find_executable('docker'):
            return True
        logger.debug('The docker command is not present, disabling the rpm plugin')
        return False

    def write_command_scripts(self):
        shutil.copyfile(pkg_resources.resource_filename(__name__, 'docker_scripts/docker_build'), 'docker_build')


    def run_package_command(self, package_hashes, wheel_dir='wheels'):
        logger.debug('Config')
        logger.debug(self.config)
        if not self.config['docker_container'].get('container_name', None):
            self.config['docker_container']['container_name'] = 'invirtualenvapp/' + self.config['global']['name']
            self.config['docker_container']['files'].append('deploy.conf /var/lib/invirtualenv/{name}/deploy.conf'.format(name=self.config['global']['name']))
        for package, hash in package_hashes.items():
            source_filename = os.path.join(wheel_dir, package)
            dest_filename = '/var/lib/invirtualenv/wheels/{name}/{package}'.format(name=self.config['global']['name'], package=package)
            self.config['docker_container']['files'].append(source_filename + ' ' + dest_filename)

        self.write_command_scripts()

        logger.debug('Dockerfile')
        logger.debug(self.render_template_with_config())
        logger.debug('Wheels')
        logger.debug(os.listdir(wheel_dir))
        with open('Dockerfile', 'w') as dockerfile_handle:
            dockerfile_handle.write(self.render_template_with_config())
        container_tag = 'invirtualenvapp/{name}:{version}'.format(name=self.config['global']['name'], version=self.config['global']['version'])
        command = [find_executable('docker'), 'build', '-t', container_tag, '.']
        logger.debug('Running command %r', ' '.join(command))
        subprocess.check_call(command)
        return container_tag
