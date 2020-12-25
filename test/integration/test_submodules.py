import json
import os

from mopack.platforms import platform_name

from . import *


class TestSubmodules(IntegrationTest):
    name = 'submodules'
    maxDiff = None

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-submodules-implicit.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertNotExists('mopack/src/hello/hello-bfg/build.bfg')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        for s in (['french'], ['english'], ['french', 'english']):
            self.assertPkgConfigUsage(
                'hello', pcfiles=['hello_' + i for i in s], submodules=s
            )
        self.assertUsage('hello', returncode=1)

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': {
                'common': {
                    'target_platform': platform_name(),
                    'env': AlwaysEqual(),
                    'deploy_paths': {},
                },
                'builders': [{
                    'type': 'bfg9000',
                    'toolchain': None,
                }],
                'sources': [],
            },
            'packages': [{
                'name': 'hello',
                'config_file': config,
                'resolved': True,
                'source': 'directory',
                'submodules': {
                    'names': ['french', 'english'],
                    'required': True,
                },
                'should_deploy': True,
                'builder': {
                    'type': 'bfg9000',
                    'name': 'hello',
                    'extra_args': [],
                    'usage': {
                        'type': 'pkg-config',
                        'path': {'base': 'builddir', 'path': 'pkgconfig'},
                        'pcfile': None,
                        'extra_args': [],
                        'submodule_map': {
                            '*': {'pcfile': {'#phs#': ['hello_', 0]}},
                        },
                    },
                },
                'path': {'base': 'cfgdir', 'path': 'hello-multi-bfg'},
            }],
        })
