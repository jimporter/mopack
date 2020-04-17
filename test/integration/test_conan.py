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

        output = json.loads(self.assertPopen([
            'mopack', 'usage', 'zlib', '--json'
        ]))
        self.assertEqual(output, {
            'name': 'zlib',
            'type': 'pkgconfig',
            'path': os.path.join(self.stage, 'mopack', 'conan'),
        })

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata']['packages'], {
            'zlib': {
                'config': {
                    'name': 'zlib',
                    'config_file': config,
                    'source': 'conan',
                    'remote': 'zlib/1.2.11@conan/stable',
                    'options': {'shared': True},
                    'usage': {'type': 'pkgconfig', 'path': '.'}
                },
                'usage': {
                    'type': 'pkgconfig',
                    'path': os.path.join(self.stage, 'mopack', 'conan')
                },
            },
        })
