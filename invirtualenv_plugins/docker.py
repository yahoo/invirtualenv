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

{% if docker_container['workdir_start'] %}WORKDIR {{docker_container['workdir_start']}}
{% endif -%}
{% if docker_container['add'] or docker_container['files'] or docker_container['copy'] %}# Files
{% endif -%}
{%- if docker_container['add'] %}{% for file_line in docker_container['add'] %}ADD {{file_line}}
{% endfor %}{% endif -%}
{%- if docker_container['files'] %}{% for file_line in docker_container['files'] %}COPY {{file_line}}
{% endfor %}{% endif -%}
{%- if docker_container['copy'] %}{% for file_line in docker_container['copy'] %}COPY {{file_line}}
{% endfor %}{% endif -%}
{%- if docker_container['add'] or docker_container['files'] or docker_container['copy'] %}
{% endif -%}
{% if docker_container['setenv'] or docker_container['env'] %}# Environment Settings
{% endif -%}{% if docker_container['setenv'] %}{% for setting, value in docker_container['setenv'].items() %}ENV {{setting}}="{{value}}"
{% endfor %}{% endif -%}
{%- if docker_container['env'] %}{% for setting, value in docker_container['env'].items() %}ENV {{setting}}="{{value}}"
{% endfor %}{% endif -%}
{%- if docker_container['env'] or docker_container['setenv'] %}
{% endif -%}
{% if docker_container['expose'] %}# Ports
{% for expose_port in docker_container['expose'] %}EXPOSE {{expose_port}}
{% endfor %}{% endif -%}
{%- if docker_container['expose'] %}
{% endif -%}
{% if docker_container['label'] %}# Labels
{% for label in docker_container['label'] %}LABEL {{label}}
{% endfor %}{% endif -%}
{%- if docker_container['label'] %}
{% endif -%}
{%- if docker_container['volume'] %}# Volumes
{% for volume in docker_container['volume'] %}VOLUME {{volume}}
{% endfor %}{% endif -%}
{%- if docker_container['volume'] %}
{% endif -%}
{%- if docker_container['run_before'] %}# Pre Invirtulenv Commands
{% for runline in docker_container['run_before'] %}RUN {{runline}}
{% endfor %}{% endif -%}
{%- if docker_container['run_before'] %}
{% endif -%}
# Set up invirtualenv in the container
ENV PATH="/var/lib/invirtualenv/installvenv/bin:${PATH}"
COPY docker_build.sh /tmp/docker_build.sh
COPY deploy.conf /var/lib/invirtualenv/deploy.conf
RUN chmod 755 /tmp/docker_build.sh
RUN /tmp/docker_build.sh
RUN rm /tmp/docker_build.sh

{% if docker_container['run_after'] %}# Post Invirtualenv Commands
{% for runline in docker_container['run_after'] %}RUN {{runline}}
{% endfor %}{% endif -%}
{%- if docker_container['run_after'] %}
{% endif -%}

{% if docker_container['entrypoint'] %}ENTRYPOINT {{docker_container['entrypoint']}}
{% endif -%}
{% if docker_container['cmd'] %}CMD {{docker_container['cmd']}}
{% endif -%}
{% if docker_container['healthcheck'] %}HEALTHCHECK {{docker_container['healthcheck']}}
{% endif -%}
{% if docker_container['stopsignal'] %}STOPSIGNAL {{docker_container['stopsignal']}}
{% endif -%}
{% if docker_container['user'] %}USER {{docker_container['user']}}
{% endif -%}
"""

DOCKER_CONFIG_DEFAULT = """[docker_container]
add=
base_image=ubuntu:17.10
cmd=
container_name=
copy:
entrypoint=
env:
expose:
deb_deps:
files:
healthcheck=
label:
rpm_deps:
run_before:
run_after:
setenv:
stopsignal=
user=
volume:
workdir_start=
"""


class InvirtualenvDocker(InvirtualenvPlugin):
    package_formats = ['docker']
    package_template = DOCKERFILE_TEMPLATE
    config_default = DOCKER_CONFIG_DEFAULT
    default_config_filename = 'Dockerfile.invirtualenv'
    config_types = {
        'docker_container': {
            'add': list,
            'base_image': str,
            'container_name': str,
            'cmd': str,
            'copy': list,
            'deb_deps': list,
            'entrypoint': str,
            'env': str_to_dict,
            'expose': list,
            'files': list,
            'healthcheck': str,
            'label': list,
            'rpm_deps': list,
            'run_before': list,
            'run_after': list,
            'setenv': str_to_dict,
            'stopsignal': str,
            'user': str,
            'volume': list,
            'workdir_start': str,
        }
    }

    def system_requirements_ok(self):
        if find_executable('docker'):
            return True
        logger.debug('The docker command is not present, disabling the rpm plugin')
        return False

    def generate_wheel_archive(self, filename=None):
        # For docker containers we don't use wheels
        pass

    def write_command_scripts(self):
        shutil.copyfile(pkg_resources.resource_filename(__name__, 'docker_scripts/docker_build.sh'), 'docker_build.sh')

    def generate_wheel_packages(self, wheeldir):
        # For docker containers there is no need to generate and store wheels
        return {}

    def run_package_command(self, package_hashes, wheel_dir='wheels'):
        logger.debug('Config')
        logger.debug(self.config)
        if not self.config['docker_container'].get('container_name', None):
            self.config['docker_container']['container_name'] = 'invirtualenvapp/' + self.config['global']['name']
        self.config['docker_container']['files'].append('deploy.conf /var/lib/invirtualenv/deploy.conf')
        for package, hash in package_hashes.items():
            source_filename = os.path.join(wheel_dir, package)
            dest_filename = '/var/lib/invirtualenv/wheels/{name}/{package}'.format(name=self.config['global']['name'], package=package)
            self.config['docker_container']['files'].append(source_filename + ' ' + dest_filename)

        self.write_command_scripts()

        logger.debug('Dockerfile')
        logger.debug(self.render_template_with_config())
        with open('Dockerfile', 'w') as dockerfile_handle:
            dockerfile_handle.write(self.render_template_with_config())
        container_tag = '{name}:{version}'.format(name=self.config['docker_container']['container_name'], version=self.config['global']['version'])
        command = [find_executable('docker'), 'build', '-t', container_tag, '.']
        logger.debug('Running command %r', ' '.join(command))
        subprocess.check_call(command)
        return container_tag
