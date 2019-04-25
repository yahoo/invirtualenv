#!/usr/bin/env python
# Copyright (c) 2016, Yahoo Inc.
# Copyrights licensed under the BSD License
# See the accompanying LICENSE.txt file for terms.
import os
import mock
import unittest
from invirtualenv.contextmanager import InTemporaryDirectory
from invirtualenv.plugin_base import InvirtualenvPlugin


deploy_conf = """[global]
name = test
basepython = python

[pip]
deps:
    invirtualenv
"""
deploy_conf_pip = """[global]
name = test
basepython = python
basepip = /opt/python/bin/pip2.7

[pip]
deps:
    invirtualenv
"""


class TestPluginBase(unittest.TestCase):

    def test__base__generate_wheels(self):
        with InTemporaryDirectory():
            with open('deploy.conf', 'w') as config_handle:
                config_handle.write(deploy_conf)
            plugin = InvirtualenvPlugin()
            plugin.hash = 'sha512'
            hashes = plugin.generate_wheel_packages(wheeldir=os.getcwd())
            packages = [filename.split('-')[0] for filename in hashes.keys()]
            self.assertGreater(len(hashes), 0)
            self.assertIn('invirtualenv', packages)
            self.assertIn('sha512:', list(hashes.values())[0])

    @mock.patch('subprocess.check_call')
    def test_pip_cmd(self, mock_check_call):
        with InTemporaryDirectory():
            with open('deploy.conf', 'w') as config_handle:
                config_handle.write(deploy_conf_pip)
            plugin = InvirtualenvPlugin()
            mock_check_call.return_value = 0
            self.assertEqual(u'/opt/python/bin/pip2.7', plugin.pip_cmd[1])
