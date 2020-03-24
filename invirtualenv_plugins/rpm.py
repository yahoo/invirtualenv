import os
import json
import logging
import subprocess
import pkgutil

import distro

from invirtualenv.plugin_base import InvirtualenvPlugin
from invirtualenv.utility import find_executable


logger = logging.getLogger(__name__)


SPEC_TEMPLATE = """Summary: {{global['description']|default('No summary available')}}
Name: {{global['name']}}
Version: {{global['version']|default('0.0.0')}}
Release: {{rpm_package['release']|default('1')}}
License: {{rpm_package['license']|default('Closed Source')}}
Group: {{rpm_package['group']|default('Development')}}
Packager: {{rpm_package['packager']|default('Verizon')}}
URL: {{global['url']|default('https://github.com/yahoo/invirtualenv')}}
AutoReqProv: no
{% if rpm_package['noarch'] %}BuildArch: noarch{% endif %}
{% if rpm_package['bootstrap_deps'] %}
# Install deps for {{ global['distro.name()'] }} {{ global['distro.major_version()'] }}.{{global['distro.minor_version()']}}
Requires(post): {% for package in rpm_package['bootstrap_deps'] %}{{package}}{{ ", " if not loop.last }}{% endfor %}
{% endif %}{% if rpm_package['deps'] %}
# RPM Package dependencies
Requires: {% for package in rpm_package['deps'] %}{{package}}{{ ", " if not loop.last }}{% endfor %}{% endif %}

%description
{{rpm_package['description']|default('No description')}}

%install
mkdir -p %{buildroot}/usr/share/%{name}_%{version}/
mkdir -p %{buildroot}/usr/share/%{name}_%{version}/package_scripts/
cp -r {{rpm_package['cwd']}}/wheels %{buildroot}/usr/share/%{name}_%{version}
cp {{rpm_package['cwd']}}/deploy.conf %{buildroot}/usr/share/%{name}_%{version}/deploy.conf
cp {{rpm_package['cwd']}}/post_install.py %{buildroot}/usr/share/%{name}_%{version}/package_scripts/post_install.py
cp {{rpm_package['cwd']}}/pre_uninstall.py %{buildroot}/usr/share/%{name}_%{version}/package_scripts/pre_uninstall.py
chmod 755 %{buildroot}/usr/share/%{name}_%{version}/package_scripts/post_install.py
chmod 755 %{buildroot}/usr/share/%{name}_%{version}/package_scripts/pre_uninstall.py

%post
export RPM_ARG="$1"
export PATH=$PATH:/opt/python/bin:/usr/local/bin
export PIP_CMD="pip"

# Bootstrap a Python virtualenv with the invirtualenv utility deployed in it
{{rpm_package['basepython']}} -m venv "/usr/share/%{name}_%{version}/invirtualenv_deployer"
RC="$?"
if [ "$RC" != "0" ]; then
    virtualenv -p {{rpm_package['basepython']}} /usr/share/%{name}_%{version}/invirtualenv_deployer
fi

/usr/share/%{name}_%{version}/invirtualenv_deployer/bin/$PIP_CMD install --find-links=/usr/share/%{name}_%{version}/wheels invirtualenv configparser

# Change into the directory containing this package's invirtualenv deployment configuration and run the invirtualenv_deployer
# to deploy the application in this rpm package.
cd /usr/share/%{name}_%{version}
/usr/share/%{name}_%{version}/invirtualenv_deployer/bin/python /usr/share/%{name}_%{version}/package_scripts/post_install.py

%preun
export RPM_ARG="$1"
/usr/share/%{name}_%{version}/invirtualenv_deployer/bin/python /usr/share/%{name}_%{version}/package_scripts/pre_uninstall.py

%postun
rm -rf /usr/share/%{name}_%{version}

%files
%defattr(0755, root, root, 0755)
/usr/share/%{name}_%{version}/*
{% if rpm_package['files'] %}
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
            'deps': list,
        }
    }
    default_config_filename = 'invirtualenv.spec'

    def add_plugin_configuration(self):
        # Make sure the configuration is sane
        # self.config['rpm_package']['deps'].append('invirtualenv')
        self.config['rpm_package']['cwd'] = os.getcwd()
        self.config['rpm_package']['noarch'] = self.noarch
        description = self.config['global'].get('description', '').strip()
        if not description:
            self.config['global']['description'] = 'No description available'

        basepython = self.config['rpm_package'].get('basepython', '').strip()
        gbasepython = self.config['global'].get('basepython', '').strip()
        if not basepython and gbasepython:
            self.config['rpm_package']['basepython'] = gbasepython
            self.config['global']['basepython'] = gbasepython

        # In some cases distro returns an empty string '' instead of 0, so we can't assume the value returned from
        # the calls to get that information is always an integer.
        try:
            major = int(distro.major_version())
        except ValueError:
            major = 0

        try:
            minor = int(distro.minor_version())
        except ValueError:
            with open('/etc/system-release') as fh:
                try:
                    minor = int(fh.read().strip().split()[3].split('.')[1])
                except (IndexError, ValueError):
                    minor = 0

        self.config['global']['distro.name()'] = distro.name()
        self.config['global']['distro.major_version()'] = major
        self.config['global']['distro.minor_version()'] = minor

        if major > 7 or (major == 7 and minor > 6):
            self.config['rpm_package']['bootstrap_deps'] = ['python3', 'python3-pip']  # RHEL 7.7 and newer
        else:
            self.config['rpm_package']['bootstrap_deps'] = ['python', 'python-pip', 'python-virtualenv']  # RHEL releases before 7.6

    def system_requirements_ok(self):
        if find_executable('rpmbuild'):
            return True
        logger.debug('The rpmbuild command is not present, disabling the rpm plugin')
        return False

    def run_package_command(self, package_hashes, wheel_dir='wheels'):
        self.config['rpm_package']['cwd'] = os.getcwd()

        # Get the packaging script
        for script in ['rpm_scripts/post_install.py', 'rpm_scripts/pre_uninstall.py']:
            with open(os.path.basename(script), 'wb') as script_handle:
                script_handle.write(pkgutil.get_data('invirtualenv_plugins', script))

        logger.debug('Config')
        logger.debug(json.dumps(self.config, indent=4))
        logger.debug('Spec')
        logger.debug(self.render_template_with_config())
        logger.debug('Deploy.conf')
        logger.debug(open('deploy.conf').read())
        print(f'CWD: {os.getcwd()}')
        os.system('ls -lR')
        with open('package.spec', 'w') as spec_handle:
            spec_handle.write(self.render_template_with_config())
        command = [find_executable('rpmbuild'), '-ba', 'package.spec']
        logger.debug('Running command %r', ' '.join(command))
        output = subprocess.check_output(command, env={'LANG': 'C'})
        output = output.decode(errors='ignore')
        packages = []
        for line in output.split('\n'):
            line = line.strip()
            if line.startswith('Wrote: '):
                packages.append(line.split()[-1])
        logger.debug('found packages %r', packages)
        if packages:
            return packages[-1]
