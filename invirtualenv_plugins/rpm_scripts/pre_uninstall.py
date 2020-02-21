#!/usr/bin/env python3
from __future__ import print_function
import json
import logging
import os
import shutil
import sys
from invirtualenv.deploy import unlink_deployed_bin_files
from invirtualenv.config import get_configuration_dict


if __name__ == "__main__":
    log_level = logging.INFO
    if os.environ.get('RPM_SCRIPTLET_DEBUG', 'false').lower() in ['true', '1', 'on']:
        log_level = logging.DEBUG

    logging.basicConfig(level=log_level, format='%(asctime)s %(levelname)-5s [%(filename)s:%(lineno)d] %(message)s', datefmt='%Y%m%d:%H:%M:%S')

    logger = logging.getLogger(os.path.basename(sys.argv[0]))

    upgrade = False
    scriptlet_argument = os.environ.get('RPM_ARG', '')
    if scriptlet_argument and scriptlet_argument == '1':
        upgrade = True
    logger.debug('Running pre_uninstall %s, upgrade=%r', scriptlet_argument, upgrade)
    # logger.debug('Environment: %s' % json.dumps(dict(os.environ), indent=4))


    this_script_dir = os.path.dirname(os.path.realpath(__file__))
    path_bits = this_script_dir.split(os.path.sep)

    # Remove leading package_scripts from the path
    path_bits.remove('package_scripts')
    data_dir = os.path.sep.join(path_bits)
    deploy_conf = os.path.join(data_dir, 'deploy.conf')
    if not os.path.exists(deploy_conf):
        print("No 'deploy.conf' found.  Doing nothing", file=sys.stderr)
        sys.exit(0)

    config = get_configuration_dict(deploy_conf)
    venv_dir = config['global'].get('virtualenv_deploy_dir', None)

    if venv_dir and os.path.exists(venv_dir):
        if upgrade:
            logger.debug('Package upgrade is running, not deleting bin files to prevent removing links from the new package')
        else:
            unlink_deployed_bin_files(venv_dir)
        logger.debug('Removing virtualenv directory %r' % venv_dir)
        shutil.rmtree(venv_dir)
