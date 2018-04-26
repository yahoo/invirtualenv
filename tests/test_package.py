#!/usr/bin/env python
# Copyright (c) 2016, Yahoo Inc.
# Copyrights licensed under the BSD License
# See the accompanying LICENSE.txt file for terms.

"""
test_invirtualenv
----------------------------------

Tests for `invirtualenv` module.
"""
import os
import sys
import unittest
from invirtualenv import package


bin_dir = os.path.dirname(
    os.popen('which deploy_virtualenv.py').read().strip()
)
sys.path.append(os.path.join(os.getcwd(), 'scripts'))
sys.path.append(bin_dir)


class TestPackage(unittest.TestCase):

    def test_package_scripts_directory(self):
        result = package.package_scripts_directory()
        self.assertIsInstance(result, str)

    def test_package_versions(self):
        result = package.package_versions('invirtualenv')
        self.assertIsInstance(result, list)

    def test_strip_from_end(self):
        result = package.strip_from_end("hello.conf", '.conf')
        self.assertEqual(result, 'hello')

    def test_strip_from_end__no_suffix_found(self):
        result = package.strip_from_end("hello.baz", '.conf')
        self.assertEqual(result, 'hello.baz')

    def test_latest_package_version(self):
        result = package.latest_package_version('invirtualenv')
        self.assertIsInstance(result, str)

    def test_install_prereq_packages(self):
        result = package.install_prereq_packages(test=True)


if __name__ == '__main__':
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestPackage)
    unittest.TextTestRunner(verbosity=2).run(test_suite)
