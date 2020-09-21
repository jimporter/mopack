import json
import os
from unittest import skipIf

from mopack.platforms import platform_name

from . import *


@skipIf('apt' not in test_features,
        'skipping apt tests; add `apt` to `MOPACK_EXTRA_TESTS` to enable')
class TestApt(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('apt')

    def _usage(self, name, headers=[], libraries=[]):
        return {
            'type': 'system',
            'auto_link': False,
            'include_path': [],
            'library_path': [],
            'headers': headers,
            'libraries': libraries,
            'compile_flags': [],
            'link_flags': [],
        }

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-apt.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertExists('mopack/logs/apt.log')
        self.assertExists('mopack/mopack.json')

        output = json.loads(self.assertPopen([
            'mopack', 'usage', 'ogg', '--json'
        ]))
        self.assertEqual(output, {
            'name': 'ogg', 'type': 'system', 'auto_link': False,
            'include_path': [], 'library_path': [], 'headers': [],
            'libraries': ['ogg'], 'compile_flags': [], 'link_flags': [],
        })

        output = json.loads(self.assertPopen([
            'mopack', 'usage', 'zlib', '--json'
        ]))
        self.assertEqual(output, {
            'name': 'zlib', 'type': 'system', 'auto_link': False,
            'include_path': [], 'library_path': [], 'headers': [],
            'libraries': ['z'], 'compile_flags': [], 'link_flags': [],
        })

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'deploy_paths': {},
            'options': {
                'common': {
                    'target_platform': platform_name(),
                    'env': AlwaysEqual(),
                },
                'builders': [],
                'sources': [],
            },
            'packages': [{
                'name': 'ogg',
                'config_file': config,
                'source': 'apt',
                'submodules': None,
                'should_deploy': True,
                'remote': 'libogg-dev',
                'usage': self._usage('ogg', libraries=[
                    {'name': 'ogg', 'type': 'guess'},
                ]),
            }, {
                'name': 'zlib',
                'config_file': config,
                'source': 'apt',
                'submodules': None,
                'should_deploy': True,
                'remote': 'zlib1g-dev',
                'usage': self._usage('zlib', libraries=[
                    {'name': 'zlib', 'type': 'guess'},
                ]),
            }],
        })
