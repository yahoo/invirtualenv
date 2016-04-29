#!/usr/bin/env python
# Copyright (c) 2016, Yahoo Inc.
# Copyrights licensed under the BSD License
# See the accompanying LICENSE.txt file for terms.

"""
test_invirtualenv
----------------------------------

Tests for `invirtualenv` module.
"""
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import os
import sys
import unittest
from invirtualenv import utility


class TestUtility(unittest.TestCase):
    stdout_orig = sys.stdout

    def setUp(self):
        sys.stdout = StringIO()

    def tearDown(self):
        sys.stdout = self.stdout_orig

    def test_update_recursive(self):
        dict1 = {
            'a': {
                'b': {
                    'items': [1, 2]
                }
            },
            'c': 'd'
        }
        dict2 = {
            'a': {
                'b': {
                    'otheritems': [3, 4]
                },
            },
            'c': 'e'
        }
        expected_result = {
            'a': {
                'b': {
                    'items': [1, 2],
                    'otheritems': [3, 4]
                }
            },
            'c': 'e'
        }
        result = utility.update_recursive(dict1, dict2)
        self.assertDictEqual(result, expected_result)

    def test_utility_header(self):
        utility.display_header('Test message')
        output = sys.stdout.getvalue()
        sys.stdout = self.stdout_orig
        self.assertIn('===', output)
        self.assertIn(os.linesep + 'Test message', output)
        self.assertEqual(
            len(output.split(os.linesep)),
            4,
            'Output of %r is not a single line' % output
        )

    def test_utility_header__collapse(self):
        utility.display_header('Test message', collapse=True)
        output = sys.stdout.getvalue()
        self.assertIn('===', output)
        self.assertIn('Test message', output)
        self.assertEqual(
            len(output.split(os.linesep)),
            2,
            'Output of %r is not a single line' % output
        )

    def test__str_format_env__substitue(self):
        env_value = 'foo'
        os.environ['str_format_env'] = env_value
        result = utility.str_format_env('{{str_format_env}}')
        self.assertEqual(result, env_value)
        del os.environ['str_format_env']

    def test__str_to_env_to_list(self):
        env_value = 'foo'
        os.environ['str_format_env'] = env_value
        result = utility.str_format_env('bar')
        self.assertEqual(result, 'bar')
        del os.environ['str_format_env']

    def test__csv_list(self):
        result = utility.csv_list('1,2')
        self.assertEqual(result, ['1', '2'])


if __name__ == '__main__':
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestUtility)
    unittest.TextTestRunner(verbosity=2).run(test_suite)
