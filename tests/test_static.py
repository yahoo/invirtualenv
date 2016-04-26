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
import shutil
import sys
import tempfile
import unittest
from invirtualenv.deploy import build_deploy_virtualenv
from invirtualenv import static


class TestStatic(unittest.TestCase):
    orig_sysargv = None

    def setUp(self):
        self.orig_sysargv = sys.argv
        self.tempdir = tempfile.mkdtemp()
        self.venv_dir = os.path.join(self.tempdir, 'test_static')
        if os.path.exists(self.venv_dir):
            shutil.rmtree(self.venv_dir)

    def tearDown(self):
        if self.orig_sysargv:
            sys.argv = self.orig_sysargv
            del self.orig_sysargv
        if self.venv_dir:
            if os.path.exists(self.venv_dir):
                shutil.rmtree(self.venv_dir)
            self.venv_dir = None

    @unittest.skip
    def test_python_scripts_in_virtualenv_dir(self):
        sys.argv = ['foo']
        current_dir = os.path.dirname(__file__)
        test_fixture_filename = os.path.join(
            current_dir,
            'fixtures/test_static_list_binaries.conf'
        )
        test_fixture = open(test_fixture_filename).read().format(
            **{'virtualenv_dir': self.tempdir}
        )
        with tempfile.NamedTemporaryFile() as tempfile_handle:
            tempfile_handle.write(test_fixture.encode())
            tempfile_handle.flush()
            tempfile_handle.seek(0)

            venv_dir = build_deploy_virtualenv(
                configuration=[tempfile_handle.name],
                update_existing=False,
                verbose=False
            )
            bin_dir = os.path.join(venv_dir, 'bin')
            result = static.python_scripts_in_venv_bin(venv_dir)
            if venv_dir:
                shutil.rmtree(venv_dir)
        print(result)

        self.assertEquals(result, [os.path.join(bin_dir, 'hello_world')])


if __name__ == '__main__':
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestStatic)
    unittest.TextTestRunner(verbosity=2).run(test_suite)
