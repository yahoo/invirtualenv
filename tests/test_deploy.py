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
import json
import os
import pwd
import shutil
import subprocess
import sys
import tempfile
import unittest
from invirtualenv import deploy
from invirtualenv.contextmanager import TemporaryDirectory


class TestDeploy(unittest.TestCase):
    orig_sysargv = None
    maxDiff = None
    verbose = True

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
                "[global]\nname=%s\nvirtualenv_dir=%s\n"
                "[pip]\ndeps:\n    pip\n" % (
                    venv_name,
                    self.venv_dir
                )
            )
        deploy.build_deploy_virtualenv(
            configuration=[config_file],
            verbose=self.verbose
        )
        self.assertTrue(os.path.isdir(venv_path))

    def test__build_deploy_virtualenv__no_pips(self):
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
            verbose=self.verbose
        )
        self.assertTrue(os.path.isdir(venv_path))
        confdir = os.path.join(venv_path, 'conf')
        self.assertTrue(os.path.isdir(confdir))
        self.assertTrue(
            os.path.exists(
                os.path.join(confdir, 'binfiles_predeploy.json')
            )
        )

    def test__build_deploy_virtualenv__pips(self):
        sys.argv = ['foo']
        venv_name = 'deploy_default'
        venv_path = os.path.join(self.venv_dir, venv_name)
        config_file = os.path.join(self.venv_dir, 'deploy_default.conf')
        with open(config_file, 'w') as config_handle:
            config_handle.write(
                "[global]\nname=%s\nvirtualenv_dir=%s\n"
                "[pip]\ndeps=serviceping<18.0.0\n" % (
                    venv_name,
                    self.venv_dir
                )
            )
        deploy.build_deploy_virtualenv(configuration=[config_file], verbose=self.verbose)
        self.assertTrue(os.path.isdir(venv_path))
        confdir = os.path.join(venv_path, 'conf')
        predeploy_file = os.path.join(confdir, 'binfiles_predeploy.json')
        postdeploy_file = os.path.join(confdir, 'binfiles_postdeploy.json')
        self.assertTrue(os.path.isdir(confdir))
        print(os.listdir(confdir))
        self.assertTrue(os.path.exists(predeploy_file))
        self.assertTrue(os.path.exists(postdeploy_file))
        with open(predeploy_file, 'r') as predeploy_handle:
            predeploy = json.load(predeploy_handle)
            print('predeploy', predeploy)
            self.assertIsInstance(predeploy, dict)
        with open(postdeploy_file, 'r') as postdeploy_handle:
            postdeploy = json.load(postdeploy_handle)
            print('postdeploy', postdeploy)
            self.assertIsInstance(postdeploy, dict)
        self.assertEqual(list(deploy.deployed_bin_files(venv_path).keys()), ['serviceping'])

    @unittest.skipUnless(os.getuid() == 0, "This test requires root")
    def test__build_deploy_virtualenv__pips__linkbins(self):
        sys.argv = ['foo']
        venv_name = 'deploy_default'
        venv_path = os.path.join(self.venv_dir, venv_name)
        config_file = os.path.join(self.venv_dir, 'deploy_default.conf')
        with open(config_file, 'w') as config_handle:
            config_handle.write(
                "[global]\nname=%s\nvirtualenv_dir=%s\n"
                "[pip]\ndeps=serviceping<18.0.0\n" % (
                    venv_name,
                    self.venv_dir
                )
            )
        deploy.build_deploy_virtualenv(
            configuration=[config_file],
            verbose=self.verbose
        )
        with TemporaryDirectory() as bindir:
            deploy.link_deployed_bin_files(venv_path, bindir)
            self.assertIn('serviceping', os.listdir(bindir))
            deploy.unlink_deployed_bin_files(venv_path)
            self.assertEqual([], os.listdir(bindir))

    def test__build_deploy_virtualenv__package_tools__up_to_date(self):
        sys.argv = ['foo']
        venv_name = 'deploy_default'
        venv_path = os.path.join(self.venv_dir, venv_name)
        venv_bin_dir = os.path.join(venv_path, 'bin')
        venv_pip = os.path.join(venv_bin_dir, 'pip')
        config_file = os.path.join(self.venv_dir, 'deploy_default.conf')
        major_versions = {
            'pip': 9,
            'setuptools': 36
        }
        with open(config_file, 'w') as config_handle:
            config_handle.write(
                "[global]\nname=%s\nvirtualenv_dir=%s\n"
                "[pip]\ndeps=serviceping<18.0.0\n" % (
                    venv_name,
                    self.venv_dir
                )
            )
        deploy.build_deploy_virtualenv(configuration=[config_file], verbose=self.verbose)
        output = subprocess.check_output([venv_pip, 'list', '--format=columns'])
        for line in output.decode().split(os.linesep):
            try:
                package, version = line.split()
            except ValueError:
                continue
            package = package.strip()
            if package in major_versions.keys():
                version = version.strip('(').strip(')')
                major = int(version.split('.')[0])
                self.assertGreaterEqual(major, major_versions[package])


if __name__ == '__main__':
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestDeploy)
    unittest.TextTestRunner(verbosity=2).run(test_suite)
