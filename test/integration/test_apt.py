import json
import os
from unittest import skipIf

from mopack.platforms import platform_name

from . import *


@skipIf(os.getenv('MOPACK_TEST_APT') not in ['1', 'true'],
        'skipping apt tests; set MOPACK_TEST_APT=1 to enable')
class TestApt(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('apt')

    def _usage(self, name, headers=[], libraries=[]):
        return {
            'type': 'system',
            'include_path': [],
            'library_path': [],
            'headers': headers,
            'libraries': libraries,
        }

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-apt.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertExists('mopack/apt.log')
        self.assertExists('mopack/mopack.json')

        output = json.loads(self.assertPopen([
            'mopack', 'usage', 'ogg', '--json'
        ]))
        self.assertEqual(output, {
            'name': 'ogg', 'type': 'system', 'include_path': [],
            'library_path': [], 'headers': [], 'libraries': ['ogg'],
        })

        output = json.loads(self.assertPopen([
            'mopack', 'usage', 'zlib', '--json'
        ]))
        self.assertEqual(output, {
            'name': 'zlib', 'type': 'system', 'include_path': [],
            'library_path': [], 'headers': [], 'libraries': ['z'],
        })

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'deploy_paths': {},
            'options': {
                'common': {'target_platform': platform_name()},
                'builders': [],
                'sources': [],
            },
            'packages': [{
                'name': 'ogg',
                'config_file': config,
                'source': 'apt',
                'submodules': None,
                'remote': 'libogg-dev',
                'usage': self._usage('ogg', libraries=[
                    {'name': 'ogg', 'type': 'guess'},
                ]),
            }, {
                'name': 'zlib',
                'config_file': config,
                'source': 'apt',
                'submodules': None,
                'remote': 'zlib1g-dev',
                'usage': self._usage('zlib', libraries=[
                    {'name': 'zlib', 'type': 'guess'},
                ]),
            }],
        })
