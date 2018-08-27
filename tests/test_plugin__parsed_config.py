#!/usr/bin/env python
# Copyright (c) 2016, Yahoo Inc.
# Copyrights licensed under the BSD License
# See the accompanying LICENSE.txt file for terms.
import os
import unittest
from invirtualenv.contextmanager import InTemporaryDirectory
from invirtualenv_plugins.parsedconfig import InvirtualenvParsedConfig


deploy_conf = """[global]
name = test
basepython = python

[pip]
deps:
    invirtualenv
"""


class TestPluginBase(unittest.TestCase):
    def test__config_file__argument(self):
        with InTemporaryDirectory():
            with open('deploy.conf', 'w') as config_handle:
                config_handle.write(deploy_conf)
            plugin = InvirtualenvParsedConfig(config_file='deploy.conf')
            self.assertEqual(plugin.config_file, 'deploy.conf')
            self.assertEqual(plugin.config['global']['name'], 'test')
