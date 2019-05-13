import os
import logging
import subprocess
import pkgutil
from invirtualenv.plugin_base import InvirtualenvPlugin
from invirtualenv.utility import find_executable


logger = logging.getLogger(__name__)


SPEC_TEMPLATE = """Summary: {{global['description']|default('No summary available')}}
Name: {{global['name']}}
Version: {{global['version']|default('0.0.0')}}
Release: {{rpm_package['release']|default('1')}}
License: {{rpm_package['license']|default('Closed Source')}}
Group: {{rpm_package['group']|default('Development')}}
{% if rpm_package['deps'] %}Requires: {% for package in rpm_package['deps'] %}{{package}}{{ ", " if not loop.last }}{% endfor %}{% endif %}
Packager: {{rpm_package['packager']|default('VerizonMedia')}}
URL: {{global['url']|default('https://github.com/yahoo/invirtualenv')}}
AutoReqProv: no
BuildArch: noarch
Requires(post): {{global['basepython']}}
Requires(post): /usr/bin/which

%description
{{rpm_package['description']|default('No description')}}

%install
mkdir -p %{buildroot}/usr/share/%{name}-%{version}/
mkdir -p %{buildroot}/usr/share/%{name}-%{version}/package_scripts/
cp -r {{rpm_package['cwd']}}/wheels %{buildroot}/usr/share/%{name}-%{version}
cp {{rpm_package['cwd']}}/deploy.conf %{buildroot}/usr/share/%{name}-%{version}/deploy.conf
cp {{rpm_package['cwd']}}/post_install.py %{buildroot}/usr/share/%{name}-%{version}/package_scripts/post_install.py
cp {{rpm_package['cwd']}}/pre_uninstall.py %{buildroot}/usr/share/%{name}-%{version}/package_scripts/pre_uninstall.py
chmod 755 %{buildroot}/usr/share/%{name}-%{version}/package_scripts/post_install.py
chmod 755 %{buildroot}/usr/share/%{name}-%{version}/package_scripts/pre_uninstall.py

%post
export PATH=$PATH:/opt/python/bin:/usr/local/bin
virtualenv_path=`which virtualenv ||:`
if [ -z $virtualenv_path ]
then
    # NOTE(saga): Virtualenv binary not found. Try and use python3's virtualenv
    # module. However it doesn't support specifying custom python_exe path (-p)
    python3 -m venv /usr/share/%{name}-%{version}/invirtualenv_deployer
else
    $virtualenv_path -p {{global['basepython']}} /usr/share/%{name}-%{version}/invirtualenv_deployer
fi
/usr/share/%{name}-%{version}/invirtualenv_deployer/bin/pip install -q --no-index --find-links=/usr/share/%{name}-%{version}/wheels invirtualenv configparser
cd /usr/share/%{name}-%{version}
#/usr/share/%{name}-%{version}/invirtualenv_deployer/bin/deploy_virtualenv
/usr/share/%{name}-%{version}/invirtualenv_deployer/bin/python /usr/share/%{name}-%{version}/package_scripts/post_install.py

%preun
/usr/share/%{name}-%{version}/invirtualenv_deployer/bin/python /usr/share/%{name}-%{version}/package_scripts/pre_uninstall.py

%postun
rm -rf /usr/share/%{name}-%{version}

%files
%defattr(0755, root, root)
/usr/share/%{name}-%{version}/*
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
            'deps': list
        }
    }
    default_config_filename = 'invirtualenv.spec'

    def system_requirements_ok(self):
        if find_executable('rpmbuild'):
            return True
        logger.debug('The rpmbuild command is not present, disabling the rpm plugin')
        return False

    def run_package_command(self, package_hashes, wheel_dir='wheels'):
        # Make sure the configuration is sane
        # self.config['rpm_package']['deps'].append('invirtualenv')
        self.config['rpm_package']['cwd'] = os.getcwd()
        description = self.config['global'].get('description', '').strip()
        if not description:
            self.config['global']['description'] = 'No description available'

        # Get the packaging script
        for script in ['rpm_scripts/post_install.py', 'rpm_scripts/pre_uninstall.py']:
            with open(os.path.basename(script), 'wb') as script_handle:
                script_handle.write(pkgutil.get_data('invirtualenv_plugins', script))

        logger.debug('Config')
        logger.debug(self.config)
        logger.debug('Spec')
        logger.debug(self.render_template_with_config())
        logger.debug('Deploy.conf')
        logger.debug(open('deploy.conf').read())
        with open('package.spec', 'w') as spec_handle:
            spec_handle.write(self.render_template_with_config())
        os.system('ls -lR')
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
