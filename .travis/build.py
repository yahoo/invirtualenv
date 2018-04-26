#!/usr/bin/env python
from __future__ import print_function
import os
import subprocess
import sys


def run_tox_env(env_name):
    command = ['tox', '-e', env_name]
    print('Running:' + ' '.join(command))
    try:
      subprocess.call(command)
      return 0
    except subprocess.CalledProcessError as commandfail:
      print('Tox failed with return code: %d' % commandfail.returncode)
      return commandfail.returncode


if __name__ == '__main__':
    version = os.environ.get('TRAVIS_PYTHON_VERSION', '2.7')
    print('PYTHON_VERSION: ' + version)

    test_env = version
    if version not in ['pypy', 'pypy3']:
      test_env = 'py' + version.replace('.', '')

    if version == '2.7':
        result = run_tox_env('pycodestyle')
        if result:
            sys.exit(result)

    sys.exit(run_tox_env(test_env))
