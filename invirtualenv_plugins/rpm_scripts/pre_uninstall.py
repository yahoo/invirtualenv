#!/usr/bin/env python3
from __future__ import print_function
import logging
import os
import shutil
import sys
from invirtualenv.deploy import unlink_deployed_bin_files
from invirtualenv.config import get_configuration_dict


if __name__ == "__main__":
    if not os.path.exists('deploy.conf'):
        print("No 'deploy.conf' found.  Doing nothing", file=sys.stderr)
        sys.exit(0)

    config = get_configuration_dict()
    venv_dir = config['global'].get('virtualenv_deploy_dir', None)

    if venv_dir and os.path.exists(venv_dir):
        unlink_deployed_bin_files(venv_dir)
        logging.debug('Removing virtualenv directory %r' % venv_dir)
        shutil.rmtree(venv_dir)
