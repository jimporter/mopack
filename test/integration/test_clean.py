import json
import os

from . import *


class TestClean(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('conan')

    def test_clean(self):
        config = os.path.join(test_data_dir, 'mopack-conan.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertExists('mopack/conan.log')
        self.assertExists('mopack/mopack.json')

        self.assertPopen(['mopack', 'clean'])
        self.assertNotExists('mopack/')
