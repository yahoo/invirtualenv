import logging
import subprocess
from jinja2 import Template

from invirtualenv.plugin_base import InvirtualenvPlugin
from invirtualenv.utility import find_executable


logger = logging.getLogger(__name__)


SPEC_TEMPLATE = """Summary: {{rpm_package['summary']}}
Name: {{global['name']}}
Version: {{global['version']}}
Release: {{rpm_package['release']|default('1')}}
License: {{rpm_package['license']|default('Closed Source')}}
Group: {{rpm_package['group']|default('Development')}}
{% if rpm_package['deps'] %}Requires: {% for package in rpm_package['deps'] %}{{package}}{{ ", " if not loop.last }}{% endfor %}{% endif %}
Packager: {{rpm_package['packager']|default('Oath')}}
URL: {{global['url']|default('https://github.com/yahoo/invirtualenv')}}
AutoReqProv: no

%description
{{rpm_package['description']|default('No description')}}

%install
mkdir -p %{buildroot}/usr/share/%{name}
cp -r ./wheels %{buildroot}/usr/share/%{name}
cp deploy.conf %{buildroot}/usr/share/%{name}/deploy.conf

%post
deploy_virtualenv /usr/share/%{name}/deploy.conf

%postun

{% if rpm_package['files'] %}
%files
/usr/share/%{name}/*
{% endif %}
"""

RPM_CONFIG_DEFAULT = """[rpm_package]
deps:
"""


class InvirtualenvRPM(InvirtualenvPlugin):
    package_formats = ['rpm']
    package_template = SPEC_TEMPLATE
    config_default = RPM_CONFIG_DEFAULT
    config_types = {
        'rpm_package': {
            'deps': list
        }
    }

    def system_requirements_ok(self):
        if find_executable('rpmbuild'):
            return True
        logger.debug('The rpmbuild command is not present, disabling the rpm plugin')
        return False

    def run_package_command(self, package_hashes, wheel_dir='wheels'):
        self.config['rpm_package']['deps'].append('invirtualenv')
        logger.debug('Config')
        logger.debug(self.config)
        logger.debug('Spec')
        logger.debug(self.render_template_with_config())
        with open('package.spec', 'w') as spec_handle:
            spec_handle.write(self.render_template_with_config())
        command = [find_executable('rpmbuild'), '-ba', 'package.spec']
        logger.debug('Running command %r', ' '.join(command))
        subprocess.check_call(command)