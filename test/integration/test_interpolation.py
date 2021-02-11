import json
import os

from . import *


class TestInterpolation(IntegrationTest):
    name = 'interpolation'

    def test_resolve_enabled(self):
        config = os.path.join(test_data_dir, 'mopack-interpolation.yml')
        self.assertPopen(['mopack', 'resolve', config],
                         extra_env={'MOPACK_TEST_EXTRA': '1'})
        self.assertNotExists('mopack/src/hello/hello-bfg/build.bfg')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigUsage('hello')

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(bfg9000={}),
            'packages': [
                cfg_directory_pkg(
                    'hello', config,
                    path={'base': 'cfgdir', 'path': 'hello-bfg'},
                    builder=cfg_bfg9000_builder(
                        'hello', extra_args=['--extra']
                    )
                )
            ],
        })

    def test_resolve_disabled(self):
        config = os.path.join(test_data_dir, 'mopack-interpolation.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertNotExists('mopack/src/hello/hello-bfg/build.bfg')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigUsage('hello')

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(bfg9000={}),
            'packages': [
                cfg_directory_pkg(
                    'hello', config,
                    path={'base': 'cfgdir', 'path': 'hello-bfg'},
                    builder=cfg_bfg9000_builder('hello')
                )
            ],
        })
