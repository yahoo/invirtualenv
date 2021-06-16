#!/usr/bin/env python
# Copyright (c) 2016, Yahoo Inc.
# Copyrights licensed under the BSD License
# See the accompanying LICENSE.txt file for terms.
import os
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


class TestPluginBase(unittest.TestCase):
    def test__base__generate_wheels(self):
        with InTemporaryDirectory():
            with open('deploy.conf', 'w') as config_handle:
                config_handle.write(deploy_conf)
            plugin = InvirtualenvPlugin()
            plugin.hash = 'sha512'
            hashes = plugin.generate_wheel_packages(wheeldir=os.getcwd())
            packages = [filename.split('=')[0] for filename in hashes.keys()]
            self.assertGreater(len(hashes), 0)
            self.assertIn('invirtualenv', packages)
            self.assertIn('sha512:', list(hashes.values())[0])
