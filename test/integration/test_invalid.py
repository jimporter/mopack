import os

from . import *


class TestInvalid(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('invalid')

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-invalid.yml')
        output = self.assertPopen(['mopack', 'resolve', config], returncode=1)
        self.assertRegex(output,
                         'error: expected an inner path\n' +
                         '  in ".+mopack-invalid.yml", line 5, column 5\n'
                         '      srcdir: \\.\\./foo\n' +
                         '      \\^\n$')
