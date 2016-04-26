#!/usr/bin/env python
"""
test_invirtualenv
----------------------------------

Tests for `invirtualenv` module.
"""
# Copyright (c) 2016, Yahoo Inc.
# Copyrights licensed under the BSD License
# See the accompanying LICENSE.txt file for terms.

import getpass
import os
import pwd
import shutil
import sys
import tempfile
import unittest
from invirtualenv import deploy


class TestDeploy(unittest.TestCase):
    orig_sysargv = None
    maxDiff = None

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

    @unittest.skipUnless(os.getuid() == 0, "This test requires root")
    def test__fix_file_ownership__as_root(self):
        venv = os.path.join(self.venv_dir, 'testvenv')
        nobody = pwd.getpwnam('nobody')
        current_user = pwd.getpwnam(getpass.getuser())
        os.makedirs(venv)
        self.assertEqual(os.stat(venv).st_uid, current_user.pw_uid)
        self.assertEqual(os.stat(venv).st_gid, current_user.pw_gid)
        deploy.fix_file_ownership(venv, nobody.pw_uid, nobody.pw_gid)
        self.assertEqual(os.stat(venv).st_uid, nobody.pw_uid)
        self.assertEqual(os.stat(venv).st_gid, nobody.pw_gid)

    def test__fix_file_ownership__as_user(self):
        venv = os.path.join(self.venv_dir, 'testvenv')
        current_user = pwd.getpwnam(getpass.getuser())
        nobody = current_user
        os.makedirs(venv)
        self.assertEqual(os.stat(venv).st_uid, current_user.pw_uid)
        self.assertEqual(os.stat(venv).st_gid, current_user.pw_gid)
        deploy.fix_file_ownership(venv, nobody.pw_uid, nobody.pw_gid)
        self.assertEqual(os.stat(venv).st_uid, nobody.pw_uid)
        self.assertEqual(os.stat(venv).st_gid, nobody.pw_gid)

    def test__build_deploy_virtualenv(self):
        sys.argv = ['foo']
        venv_name = 'deploy_default'
        venv_path = os.path.join(self.venv_dir, venv_name)
        config_file = os.path.join(self.venv_dir, 'deploy_default.conf')
        with open(config_file, 'w') as config_handle:
            config_handle.write(
                "[global]\nname=%s\nvirtualenv_dir=%s\n" % (
                    venv_name,
                    self.venv_dir
                )
            )
        deploy.build_deploy_virtualenv(
            configuration=[config_file],
            verbose=False)
        self.assertTrue(os.path.isdir(venv_path))


if __name__ == '__main__':
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestDeploy)
    unittest.TextTestRunner(verbosity=2).run(test_suite)
