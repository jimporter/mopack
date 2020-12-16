import json
import os

from mopack.platforms import platform_name

from . import *


class TestCustomBuilder(IntegrationTest):
    maxDiff = None

    def setUp(self):
        self.stage = stage_dir('custom-builder')

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-custom-builder.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertExists('mopack/src/hello/hello-bfg/build.bfg')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        output = json.loads(self.assertPopen([
            'mopack', 'usage', 'hello', '--json'
        ]))
        self.assertEqual(output, {
            'name': 'hello',
            'type': 'pkg-config',
            'path': os.path.join(self.stage, 'mopack', 'build', 'hello',
                                 'pkgconfig'),
            'pcfiles': ['hello'],
            'extra_args': [],
        })

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': {
                'common': {
                    'target_platform': platform_name(),
                    'env': AlwaysEqual(),
                    'deploy_paths': {},
                },
                'builders': [],
                'sources': [],
            },
            'packages': [{
                'name': 'hello',
                'config_file': config,
                'resolved': True,
                'source': 'tarball',
                'url': None,
                'path': ['cfgdir', 'hello-bfg.tar.gz'],
                'files': [],
                'srcdir': None,
                'guessed_srcdir': 'hello-bfg',
                'patch': None,
                'submodules': None,
                'should_deploy': True,
                'builder': {
                    'type': 'custom',
                    'name': 'hello',
                    'build_commands': [
                        ['bfg9000', 'configure', ['builddir', '']],
                        ['ninja', '-C', ['builddir', '']],
                    ],
                    'usage': {
                        'type': 'pkg-config',
                        'path': ['builddir', 'pkgconfig'],
                        'pcfile': 'hello',
                        'extra_args': [],
                    },
                },
            }],
        })
