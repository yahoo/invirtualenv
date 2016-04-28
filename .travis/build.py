#!/usr/bin/env python
from __future__ import print_function
import os
import subprocess
import sys

version = os.environ.get('TRAVIS_PYTHON_VERSION', '2.7')
print('PYTHON_VERSION: ' + version)

test_env = version
if version not in ['pypy', 'pypy3']:
  test_env = 'py' + version.replace('.', '')

command = ['tox', '-e', test_env]
print('Running:' + ' '.join(command))
try:
  subprocess.check_output(command)
  sys.exit(0)
except subprocess.CalledProcessError as commandfail:
  print('Tox failed with return code: %d' % commandfail.returncode)
  sys.exit(commandfail.returncode)
sys.exit(0)
