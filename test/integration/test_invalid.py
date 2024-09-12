import os

from . import *


class TestInvalid(IntegrationTest):
    name = 'invalid'

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-invalid.yml')
        output = self.assertPopen(mopack_cmd('resolve', config), returncode=1)
        self.assertRegex(output,
                         r'error: expected an inner path\n' +
                         r'  in ".+mopack-invalid.yml", line 5, column 13\n' +
                         r'      srcdir: \.\./foo\n' +
                         r'              \^\n$')


class TestInvalidChild(IntegrationTest):
    name = 'invalid-child'

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-invalid-child.yml')
        output = self.assertPopen(mopack_cmd('resolve', config), returncode=1)
        self.assertRegex(output,
                         r'error: bfg9000 got an unexpected keyword ' +
                         r"argument 'unknown'\n" +
                         r'  in ".+mopack.yml", line 4, column 5\n' +
                         r'      unknown: blah\n' +
                         r'      \^\n$')


class TestInvalidParent(IntegrationTest):
    name = 'invalid-parent'

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-invalid-parent.yml')
        output = self.assertPopen(mopack_cmd('resolve', config), returncode=1)
        self.assertRegex(output,
                         r"error: unknown linkage 'unknown'\n" +
                         r'  in ".+mopack-invalid-parent.yml", ' +
                         r'line 6, column 13\n' +
                         r'        type: unknown\n' +
                         r'              \^\n$')


class TestInvalidConditional(IntegrationTest):
    name = 'invalid-conditional'

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-invalid-conditional.yml')
        output = self.assertPopen(mopack_cmd('resolve', config), returncode=1)
        self.assertRegex(output,
                         r"error: undefined symbol 'unknown'\n" +
                         r'  in ".+mopack-invalid-conditional.yml", ' +
                         r'line 3, column 11\n' +
                         r'      - if: unknown\n' +
                         r'            \^\n$')


class TestInvalidListFiles(IntegrationTest):
    name = 'invalid-list-files'

    def test_list_files(self):
        self.assertOutput(['mopack', 'list-files'], '')
        self.assertPopen(mopack_cmd('list-files', '--strict'), returncode=1)
