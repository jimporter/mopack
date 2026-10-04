import os

from . import *


class TestBfg9000(IntegrationTest):
    name = 'bfg9000'

    def test_build(self):
        srcdir = os.path.join(test_data_dir, 'greeter-bfg')
        self.assertPopen(['9k', srcdir])
        self.assertPopen(['ninja'])


class TestCMake(IntegrationTest):
    name = 'cmake'

    def test_build(self):
        srcdir = os.path.join(test_data_dir, 'greeter-cmake')
        self.assertPopen(['cmake', srcdir])
        self.assertPopen(['cmake', '--build', '.', '--parallel'])
