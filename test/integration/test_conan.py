import json
import os

from . import *


class TestConan(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('conan')

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-conan.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertExists('mopack/conan.log')
        self.assertExists('mopack/mopack.json')

        output = json.loads(self.assertPopen(['mopack', 'info', 'zlib']))
        self.assertEqual(output, {'usage': 'conan'})
