import json
import os
from unittest import skipIf

from mopack.platforms import platform_name

from . import *


@skipIf('mingw-cross' not in test_features,
        'skipping cross-compilation tests; add `mingw-cross` to ' +
        '`MOPACK_EXTRA_TESTS` to enable')
class TestCross(IntegrationTest):
    name = 'cross'

    def _builder(self, name):
        return {
            'type': 'bfg9000',
            'name': name,
            'extra_args': [],
            'usage': {
                'type': 'pkg-config',
                'path': {'base': 'builddir', 'path': 'pkgconfig'},
                'pcfile': name,
                'extra_args': [],
            },
        }

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-nested.yml')
        toolchain = os.path.join(test_data_dir, 'mingw-windows-toolchain.bfg')
        self.assertPopen(['mopack', 'resolve', config,
                          '-Bbfg9000:toolchain=' + toolchain])
        self.assertExists('mopack/build/greeter/')
        self.assertExists('mopack/build/greeter/greeter.dll')
        self.assertExists('mopack/build/greeter/libgreeter.dll.a')
        self.assertExists('mopack/logs/greeter.log')
        self.assertExists('mopack/src/hello/hello-bfg/')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/build/hello/hello.dll')
        self.assertExists('mopack/build/hello/libhello.dll.a')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigUsage('greeter')
        self.assertPkgConfigUsage('hello')

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
                    'toolchain': toolchain,
                }],
                'sources': [],
            },
            'packages': [{
                'name': 'hello',
                'config_file': os.path.join(test_data_dir, 'greeter-bfg',
                                            'mopack.yml'),
                'resolved': True,
                'source': 'tarball',
                'submodules': None,
                'should_deploy': True,
                'builder': self._builder('hello'),
                'url': None,
                'path': {'base': 'cfgdir',
                         'path': os.path.join('..', 'hello-bfg.tar.gz')},
                'files': [],
                'srcdir': None,
                'guessed_srcdir': 'hello-bfg',
                'patch': None,
            }, {
                'name': 'greeter',
                'config_file': config,
                'resolved': True,
                'source': 'directory',
                'submodules': None,
                'should_deploy': True,
                'builder': self._builder('greeter'),
                'path': {'base': 'cfgdir', 'path': 'greeter-bfg'},
            }],
        })
