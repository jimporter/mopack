import json
import os

from mopack.platforms import platform_name

from . import *


class TestLocal(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('local')

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'local')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertExists('mopack/logs/conan.log')
        self.assertExists('mopack/mopack.json')

        output = json.loads(self.assertPopen([
            'mopack', 'usage', 'zlib', '--json'
        ]))
        self.assertEqual(output, {
            'name': 'zlib',
            'type': 'pkg-config',
            'path': os.path.join(self.stage, 'mopack', 'conan'),
            'pcfiles': ['zlib'],
            'extra_args': [],
        })

        self.assertOutput(['mopack', 'list-files'], (
            os.path.join(config, 'mopack.yml') + '\n' +
            os.path.join(config, 'mopack-local.yml') + '\n'
        ))
        output = json.loads(self.assertPopen(['mopack', 'list-files',
                                              '--json']))
        self.assertEqual(output, [os.path.join(config, 'mopack.yml'),
                                  os.path.join(config, 'mopack-local.yml')])

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'deploy_paths': {},
            'options': {
                'common': {
                    'target_platform': platform_name(),
                    'env': AlwaysEqual(),
                },
                'builders': [],
                'sources': [{
                    'source': 'conan',
                    'build': ['missing'],
                    'generator': ['pkg_config'],
                }],
            },
            'packages': [{
                'name': 'zlib',
                'config_file': os.path.join(config, 'mopack-local.yml'),
                'resolved': True,
                'source': 'conan',
                'submodules': None,
                'should_deploy': True,
                'remote': 'zlib/1.2.11',
                'options': {'shared': True},
                'usage': {
                    'type': 'pkg-config',
                    'path': '.',
                    'pcfile': 'zlib',
                    'extra_args': [],
                },
            }],
        })
