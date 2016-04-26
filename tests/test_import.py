#!/usr/bin/env python
# Copyright (c) 2016, Yahoo Inc.
# Copyrights licensed under the BSD License
# See the accompanying LICENSE.txt file for terms.

"""
test_invirtualenv
----------------------------------

Tests for `invirtualenv` module.
"""
import unittest


class TestImport(unittest.TestCase):

    def test_import_invirtualenv(self):
        import invirtualenv

    def test_import_invirtualenv_config(self):
        import invirtualenv.config

    def test_import_invirtualenv_deploy(self):
        import invirtualenv.deploy

    def test_import_invirtualenv_exceptions(self):
        import invirtualenv.exceptions

    def test_import_invirtualenv_package(self):
        import invirtualenv.package

    def test_import_invirtualenv_utility(self):
        import invirtualenv.utility

    def test_import_invirtualenv_virtualenv(self):
        import invirtualenv.virtualenv

    def test_import_invirtualenv_plugin(self):
        import invirtualenv.plugin


if __name__ == '__main__':
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestImport)
    unittest.TextTestRunner(verbosity=2).run(test_suite)
