import os
import unittest
import invirtualenv.contextmanager


class TestContextmanager(unittest.TestCase):
    def test__revert_file(self):
        with invirtualenv.contextmanager.InTemporaryDirectory():
            with open('testfile', 'w') as fh:
                fh.write('original')
            self.assertEqual('original', open('testfile').read())
            with invirtualenv.contextmanager.revert_file('testfile'):
                with open('testfile', 'w') as fh:
                    fh.write('changed')
                self.assertEqual('changed', open('testfile').read())
            self.assertEqual('original', open('testfile').read())

    def test__InTemporaryDir(self):
        with invirtualenv.contextmanager.InTemporaryDirectory() as tempdir:
            self.assertIsInstance(tempdir, str)
            self.assertTrue(os.path.exists(tempdir))
