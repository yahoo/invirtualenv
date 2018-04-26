#!/usr/bin/env python
# Copyright (c) 2016, Yahoo Inc.
# Copyrights licensed under the BSD License
# See the accompanying LICENSE.txt file for terms.

"""
test_invirtualenv
----------------------------------

Tests for `invirtualenv` module.
"""
import copy
import difflib
import getpass
import json
import logging
import os
import shutil
import sys
import tempfile
import unittest
from invirtualenv import config, plugin
from invirtualenv.contextmanager import InTemporaryDirectory


class TestConfig(unittest.TestCase):
    orig_sysargv = None
    maxDiff = None
    default_config_dict = {
        'global': {
            'basepython': '',
            'description': 'No description is available',
            'name': '',
            'install_os_packages': False,
            'install_manifest': [],
            'version': '',
            'virtualenv_deploy_dir': '',
            'virtualenv_dir': '/var/tmp/virtualenv',
            'virtualenv_group': '',
            'virtualenv_user': '',
            'virtualenv_version_package': ''
        },
        'pip': {
            'deps': [],
            'pip_version': '',
        },
        'rpm': {
            'deps': [],
            'fail_missing_yum': True
        },
    }

    def setUp(self):
        self.orig_sysargv = sys.argv
        self.tempdir = tempfile.mkdtemp()
        self.venv_dir = os.path.join(self.tempdir, 'test_config')
        os.makedirs(self.venv_dir)

    def tearDown(self):
        if self.orig_sysargv:
            sys.argv = self.orig_sysargv
            del self.orig_sysargv
        if self.venv_dir:
            if os.path.exists(self.venv_dir):
                shutil.rmtree(self.venv_dir)
            self.venv_dir = None

    def test_config_parse_arguments_defaults(self):
        sys.argv = ['foo', 'foo']
        result = config.parse_arguments()
        self.assertEqual(result.name, 'foo')
        self.assertEqual(result.virtualenvgroup, '')
        self.assertEqual(result.virtualenvuser, getpass.getuser())
        self.assertFalse(result.install_os_packages)

    def test_deploy_virtualenv_parse_arguments(self):
        sys.argv = [
            'deploy_virtualenv.py', 'foo',
            '-r', 'requirements_dev.txt',
            '--requirement', 'requirements.txt'
        ]
        result = config.parse_arguments()
        self.assertEqual(result.name, 'foo')
        self.assertListEqual(
            result.requirement, ['requirements_dev.txt', 'requirements.txt']
        )

    def test_config_get_configuration_dict__default(self):
        with InTemporaryDirectory():
            result = config.get_configuration_dict(
                configuration=[],
                value_types=plugin.config_types()
            )
            self.assertIsInstance(result, dict)
            if 'rpm_package' in result.keys():
                del result['rpm_package']
            if 'docker_container' in result.keys():
                del result['docker_container']

            self.assertIn(
                result['global']['virtualenv_dir'],
                [
                    '/var/tmp/virtualenv',
                    '/tmp/virtualenv'
                ]
            )
            result['global']['virtualenv_dir'] = '/var/tmp/virtualenv'

            self.assertTrue(
                result['locations']['package_scripts'].endswith('package_scripts')
            )
            del result['locations']
            result_pretty = json.dumps(result, indent=4, sort_keys=True)
            expected_pretty = json.dumps(
                self.default_config_dict, indent=4, sort_keys=True)
            diff = difflib.unified_diff(
                result_pretty.split('\n'), expected_pretty.split('\n')
            )
            logging.debug('Result: %s' % result_pretty)
            logging.debug('Expected: %s' % expected_pretty)
            logging.debug('Diff: %s' % '\n'.join(diff))
            self.assertDictEqual(result,self.default_config_dict)

    def test_config_get_configuration_dict__substitution(self):
        config_file = os.path.join(self.venv_dir, 'dict_subst.conf')
        expected = copy.copy(self.default_config_dict)
        expected['global']['version'] = '0.0.10'
        with open(config_file, 'w') as config_handle:
            config_handle.write(
                "[global]\nversion=0.0.{{DICT_SUBST|default('0')}}"
            )
        os.environ['DICT_SUBST'] = '10'
        result = config.get_configuration_dict(
            configuration=[config_file],
            value_types=plugin.config_types()
        )
        if 'rpm_package' in result.keys():
            del result['rpm_package']
        if 'docker_container' in result.keys():
            del result['docker_container']

        self.assertIsInstance(result, dict)
        self.assertIn(
            result['global']['virtualenv_dir'],
            [
                '/var/tmp/virtualenv',
                '/tmp/virtualenv'
            ]
        )
        result['global']['virtualenv_dir'] = '/var/tmp/virtualenv'

        self.assertTrue(
            result['locations']['package_scripts'].endswith('package_scripts')
        )
        del result['locations']
        result_pretty = json.dumps(result, indent=4, sort_keys=True)
        expected_pretty = json.dumps(expected, indent=4, sort_keys=True)
        diff = difflib.unified_diff(
            result_pretty.split('\n'), expected_pretty.split('\n')
        )
        logging.debug('Result: %s' % result_pretty)
        logging.debug('Expected: %s' % expected_pretty)
        logging.debug('Diff: %s' % '\n'.join(diff))
        self.assertDictEqual(result, expected)

    def test_config_str_to_list__empty(self):
        result = config.str_to_list('')
        self.assertIsInstance(result, list)
        self.assertFalse(result)

    def test_config_str_to_list__items(self):
        result = config.str_to_list('\rfoo\n')
        self.assertIsInstance(result, list)
        self.assertEqual(result, ['foo'])

    def test_generate_parsed_config_file(self):
        with tempfile.NamedTemporaryFile('w') as source_handle:
            source_handle.write('foo = {{TEST_GEN_CONF}}\n')
            source_handle.flush()
            os.environ['TEST_GEN_CONF'] = '1'
            outfile = config.generate_parsed_config_file(source_handle.name)
            with open(outfile) as out_handle:
                result = out_handle.read()
                self.assertEqual(result, 'foo = 1')
            os.remove(outfile)
            del os.environ['TEST_GEN_CONF']

    def test_plugin_package_formats(self):
        result = plugin.package_formats()
        self.assertIsInstance(result, list)


if __name__ == '__main__':
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestConfig)
    unittest.TextTestRunner(verbosity=2).run(test_suite)
