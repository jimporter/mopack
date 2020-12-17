import json
import os

from mopack.platforms import platform_name

from . import *


class TestConan(IntegrationTest):
    name = 'conan'

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-conan.yml')
        self.assertPopen(['mopack', 'resolve', '-Sconan:generator=txt',
                          config])
        self.assertExists('mopack/logs/conan.log')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigUsage('zlib', path=os.path.join(
            self.stage, 'mopack', 'conan'
        ))

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
                    'generator': ['pkg_config', 'txt', 'cmake'],
                }],
            },
            'packages': [{
                'name': 'zlib',
                'config_file': config,
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
