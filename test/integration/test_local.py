import json
import os

from mopack.platforms import platform_name

from . import *


class TestLocal(IntegrationTest):
    name = 'local'

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'local')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertExists('mopack/logs/conan.log')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigUsage('zlib', path=os.path.join(
            self.stage, 'mopack', 'conan'
        ))

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
            'options': {
                'common': {
                    'target_platform': platform_name(),
                    'env': AlwaysEqual(),
                    'deploy_paths': {},
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
                    'path': {'base': 'builddir', 'path': ''},
                    'pcfile': 'zlib',
                    'extra_args': [],
                },
            }],
        })
