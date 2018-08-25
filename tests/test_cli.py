#!/usr/bin/env python
# Copyright (c) 2016, Yahoo Inc.
# Copyrights licensed under the BSD License
# See the accompanying LICENSE.txt file for terms.

import os
import sys
import unittest
from invirtualenv.cli import parse_cli_arguments, main
from invirtualenv.contextmanager import InTemporaryDirectory
from invirtualenv.plugin import package_formats


class TestCli(unittest.TestCase):
    orig_argv = None

    def setUp(self):
        self._orig_argv = sys.argv

    def tearDown(self):
        if self.orig_argv:
            sys.argv = self._orig_argv
            sys.argv = None

    def test__parse_cli_arguments__defaults(self):
        with InTemporaryDirectory():
            with open('deploy.conf', 'w') as write_handle:
                write_handle.write('[global]\nname=foo\n')
            sys.argv = ['invirtualenv']
            if sys.version_info.major < 3:
                with self.assertRaises(SystemExit):
                    result = parse_cli_arguments()
            else:
                result = parse_cli_arguments()

    def test__main__list_plugins(self):
        with InTemporaryDirectory():
            with open('deploy.conf', 'w') as write_handle:
                write_handle.write('[global]\nname=foo\n')
            sys.argv = ['invirtualenv', 'list_plugins']
            rc, output = main(test=True)
            self.assertEqual(rc, 0)
            for plugin in package_formats():
                self.assertIn(plugin, output)

    def test__get_setting_command(self):
        with InTemporaryDirectory():
            with open('deploy.conf', 'w') as write_handle:
                write_handle.write('[global]\nname=foo\n')
            sys.argv = ['invirtualenv', 'get_setting', 'global', 'name']
            rc, output = main(test=True)
            self.assertEqual(rc, 0)
            self.assertEqual(output, 'foo')

    def test__get_setting_command_invalid_key(self):
        with InTemporaryDirectory():
            with open('deploy.conf', 'w') as write_handle:
                write_handle.write('[global]\nname=foo\n')
            sys.argv = ['invirtualenv', 'get_setting', 'global', 'namez']
            rc, output = main(test=True)
            self.assertEqual(rc, 1)
            self.assertEqual(output, '')

    def test__create_package_config__parsed_deploy_conf__outfile(self):
        with InTemporaryDirectory():
            with open('deploy.conf', 'w') as write_handle:
                write_handle.write('[global]\ntest={{TESTVAR}}\n')
            os.environ['TESTVAR'] = 'foo'
            sys.argv = ['invirtualenv', 'create_package_config', 'parsed_deploy_conf', '-o', 'deploy.conf.parsed']
            rc, output = main(test=True)
            self.assertTrue(os.path.exists('deploy.conf.parsed'))
            self.assertEqual(rc, 0)
            self.assertIn('deploy.conf.parsed', output)

    def test__create_package_config__parsed_deploy_conf__nooutfile(self):
        with InTemporaryDirectory():
            with open('deploy.conf', 'w') as write_handle:
                write_handle.write('[global]\ntest={{TESTVAR}}\n')
            os.environ['TESTVAR'] = 'foo'
            sys.argv = ['invirtualenv', 'create_package_config', 'parsed_deploy_conf']
            rc, output = main(test=True)
            self.assertTrue(os.path.exists('deploy.conf.parsed'))
            self.assertEqual(rc, 0)


if __name__ == '__main__':
    unittest.main()
