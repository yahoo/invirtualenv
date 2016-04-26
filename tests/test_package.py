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


@unittest.skip(
    'Test skipped until the invirtualenv package is on the public repos'
)
class TestPackage(unittest.TestCase):

    def test_package_versons(self):
        result = package.package_versions('invirtualenv')
        self.assertTrue(len(result[0].split('.')) == 3)


if __name__ == '__main__':
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestPackage)
    unittest.TextTestRunner(verbosity=2).run(test_suite)
