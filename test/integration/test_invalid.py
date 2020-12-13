import os

from . import *


class TestInvalid(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('invalid')

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-invalid.yml')
        output = self.assertPopen(['mopack', 'resolve', config], returncode=1)
        self.assertRegex(output,
                         r'error: expected an inner path\n' +
                         r'  in ".+mopack-invalid.yml", line 5, column 13\n' +
                         r'      srcdir: \.\./foo\n' +
                         r'              \^\n$')


class TestInvalidChild(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('invalid-child')

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-invalid-child.yml')
        output = self.assertPopen(['mopack', 'resolve', config], returncode=1)
        self.assertRegex(output,
                         r'error: bfg9000 got an unexpected keyword ' +
                         r"argument 'unknown'\n" +
                         r'  in ".+mopack.yml", line 4, column 5\n' +
                         r'      unknown: blah\n' +
                         r'      \^\n$')


class TestInvalidParent(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('invalid-parent')

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-invalid-parent.yml')
        output = self.assertPopen(['mopack', 'resolve', config], returncode=1)
        self.assertRegex(output,
                         r"error: unknown usage 'unknown'\n" +
                         r'  in ".+mopack-invalid-parent.yml", ' +
                         r'line 6, column 13\n' +
                         r'        type: unknown\n' +
                         r'              \^\n$')


class TestInvalidListFiles(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('invalid-list-files')

    def test_list_files(self):
        self.assertOutput(['mopack', 'list-files'], '')
        self.assertPopen(['mopack', 'list-files', '--strict'], returncode=1)
