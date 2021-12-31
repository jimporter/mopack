import json
import os
from unittest import skipIf

from . import *


@skipIf('mingw-cross' not in test_features,
        'skipping cross-compilation tests; add `mingw-cross` to ' +
        '`MOPACK_EXTRA_TESTS` to enable')
class TestCross(IntegrationTest):
    name = 'cross'

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
            'options': cfg_options(bfg9000={'toolchain': toolchain}),
            'packages': [
                cfg_tarball_pkg(
                    'hello',
                    os.path.join(test_data_dir, 'greeter-bfg', 'mopack.yml'),
                    parent='greeter',
                    path={'base': 'cfgdir',
                          'path': os.path.join('..', 'hello-bfg.tar.gz')},
                    guessed_srcdir='hello-bfg',
                    builder=cfg_bfg9000_builder('hello'),
                    usage=cfg_pkg_config_usage(pcname='hello')
                ),
                cfg_directory_pkg(
                    'greeter', config,
                    path={'base': 'cfgdir', 'path': 'greeter-bfg'},
                    builder=cfg_bfg9000_builder('greeter'),
                    usage=cfg_pkg_config_usage(pcname='greeter')
                ),
            ],
        })
