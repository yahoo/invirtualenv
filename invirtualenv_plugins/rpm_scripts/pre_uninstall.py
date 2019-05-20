#!/usr/bin/env python3
from __future__ import print_function
import logging
import os
import shutil
import sys
from invirtualenv.deploy import unlink_deployed_bin_files
from invirtualenv.config import get_configuration_dict


if __name__ == "__main__":
    # /usr/share/<packagename_version>/package_scripts
    this_script_dir = os.path.dirname(os.path.realpath(__file__))
    path_bits = this_script_dir.split(os.path.sep)
    # Remove leading package_scripts from the path
    path_bits.remove('package_scripts')
    # /usr/share/<packagename_version>/
    data_dir = os.path.sep.join(path_bits)
    deploy_conf = os.path.join(data_dir, 'deploy.conf')
    if not os.path.exists(deploy_conf):
        print("No 'deploy.conf' found.  Doing nothing", file=sys.stderr)
        sys.exit(0)

    config = get_configuration_dict(deploy_conf)
    venv_dir = config['global'].get('virtualenv_deploy_dir', None)

    if venv_dir and os.path.exists(venv_dir):
        unlink_deployed_bin_files(venv_dir)
        logging.debug('Removing virtualenv directory %r' % venv_dir)
        shutil.rmtree(venv_dir)
