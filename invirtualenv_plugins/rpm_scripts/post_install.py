#!/usr/bin/env python3
from __future__ import print_function
import logging
import os
import shutil
import sys

from configparser import ConfigParser, NoOptionError
from invirtualenv.deploy import build_deploy_virtualenv


def update_config(venv_dir, config_filename=None):
    if not config_filename:
        config_filename = 'deploy.conf'
    config = ConfigParser()
    config.read(config_filename)
    config.set('global', 'virtualenv_deploy_dir', venv_dir)
    with open(config_filename, 'w') as configfile:
        config.write(configfile)


def get_config_flag(section, option, config_filename=None):
    if not config_filename:
        config_filename = 'deploy.conf'
    config = ConfigParser()
    config.read(config_filename)
    try:
        return config.getboolean(section, option)
    except NoOptionError:
        return


if __name__ == "__main__":
    log_level = logging.INFO
    if os.environ.get('RPM_SCRIPTLET_DEBUG', 'false').lower() in ['true', '1', 'on']:
        log_level = logging.DEBUG

    logging.basicConfig(level=log_level, format='%(asctime)s %(levelname)-5s [%(filename)s:%(lineno)d] %(message)s', datefmt='%Y%m%d:%H:%M:%S')

    logger = logging.getLogger(os.path.basename(sys.argv[0]))

    logger.debug('Running post install steps, from directory %r' % os.getcwd())

    upgrade = False
    scriptlet_argument = os.environ.get('RPM_ARG', '')
    if scriptlet_argument and scriptlet_argument == '2':
        upgrade = True
    logger.debug('Running post_install %s, upgrade=%r', scriptlet_argument, upgrade)

    if not os.path.exists('deploy.conf'):
        print("No 'deploy.conf' found.  Doing nothing", file=sys.stderr)
        sys.exit(1)

    logger.debug('Using the following deploy.conf: %s' % open('deploy.conf').read())

    venv_directory = None
    try:
        venv_directory = build_deploy_virtualenv(update_existing=True)
        update_config(venv_directory)
    except Exception:
        print('Unable to create the python virtualenv', file=sys.stderr)
        logger.exception('The virtualenv create failed, removing venv_directory')
        if venv_directory and os.path.exists(venv_directory):
            print('Removing the %r virtualenv directory' % venv_directory)
            shutil.rmtree(venv_directory)
        sys.exit(1)

    if get_config_flag('global', 'link_bin_files'):
        logger.debug('Linking files in the virtualenv bin directory to %r', os.path.dirname(sys.executable))
        try:
            from invirtualenv.deploy import link_deployed_bin_files
            link_deployed_bin_files(venv_directory, '/usr/bin')
        except ImportError:
            print('WARNING: The installed version of invirtualenv does not support linking bin files')

    print('Created virtualenv %r' % venv_directory)
    sys.exit(0)
