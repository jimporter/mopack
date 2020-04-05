import json
import os
from unittest import skipIf

from . import *


@skipIf(os.getenv('MOPACK_TEST_APT') not in ['1', 'true'],
        'skipping apt tests; set MOPACK_TEST_APT=1 to enable')
class TestApt(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('apt')

    def test_fetch(self):
        config = os.path.join(test_data_dir, 'mopack-apt.yml')
        self.assertPopen(['mopack', 'fetch', config])
        self.assertExists('mopack/apt.log')
        self.assertExists('mopack/mopack.json')

        output = json.loads(self.assertPopen(['mopack', 'info', 'ogg']))
        self.assertEqual(output, {'usage': 'apt', 'remote': 'libogg-dev'})

        output = json.loads(self.assertPopen(['mopack', 'info', 'zlib']))
        self.assertEqual(output, {'usage': 'apt', 'remote': 'zlib1g-dev'})
