import json
import os

from . import *


class TestConan(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('conan')

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-conan.yml')
        self.assertPopen(['mopack', 'resolve', '-Sconan:generator=txt',
                          config])
        self.assertExists('mopack/conan.log')
        self.assertExists('mopack/mopack.json')

        output = json.loads(self.assertPopen([
            'mopack', 'usage', 'zlib', '--json'
        ]))
        self.assertEqual(output, {
            'name': 'zlib',
            'type': 'pkg-config',
            'path': os.path.join(self.stage, 'mopack', 'conan'),
        })

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'deploy_paths': {},
            'options': {
                'general': {'target_platform': None},
                'builders': [],
                'sources': [{
                    'source': 'conan',
                    'generator': ['pkg_config', 'txt', 'cmake'],
                }],
            },
            'packages': [{
                'name': 'zlib',
                'config_file': config,
                'source': 'conan',
                'remote': 'zlib/1.2.11@conan/stable',
                'options': {'shared': True},
                'usage': {'type': 'pkg-config', 'path': '.'}
            }],
        })
