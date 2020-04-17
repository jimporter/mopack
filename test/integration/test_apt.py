import json
import os
from unittest import skipIf

from . import *


@skipIf(os.getenv('MOPACK_TEST_APT') not in ['1', 'true'],
        'skipping apt tests; set MOPACK_TEST_APT=1 to enable')
class TestApt(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('apt')

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-apt.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertExists('mopack/apt.log')
        self.assertExists('mopack/mopack.json')

        output = json.loads(self.assertPopen([
            'mopack', 'usage', 'ogg', '--json'
        ]))
        self.assertEqual(output, {'name': 'ogg', 'type': 'system'})

        output = json.loads(self.assertPopen([
            'mopack', 'usage', 'zlib', '--json'
        ]))
        self.assertEqual(output, {'name': 'zlib', 'type': 'system'})

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata']['packages'], {
            'ogg': {
                'config': {
                    'name': 'ogg',
                    'config_file': config,
                    'source': 'apt',
                    'remote': 'libogg-dev',
                    'usage': {'type': 'system'}
                },
                'usage': {'type': 'system'},
            },
            'zlib': {
                'config': {
                    'name': 'zlib',
                    'config_file': config,
                    'source': 'apt',
                    'remote': 'zlib1g-dev',
                    'usage': {'type': 'system'}
                },
                'usage': {'type': 'system'},
            },
        })
