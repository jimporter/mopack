import os

from . import *


class TestClean(IntegrationTest):
    name = 'conan'

    def test_clean(self):
        config = os.path.join(test_data_dir, 'mopack-conan.yml')
        self.assertPopen(mopack_cmd('resolve', config))
        self.assertExists('mopack/logs/conan.log')
        self.assertExists('mopack/mopack.json')

        self.assertPopen(mopack_cmd('clean'))
        self.assertNotExists('mopack/')
