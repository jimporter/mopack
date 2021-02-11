import json
import os

from . import *


class TestSubmodules(IntegrationTest):
    name = 'submodules'

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
            'options': cfg_options(bfg9000={}),
            'packages': [
                cfg_directory_pkg(
                    'hello', config,
                    submodules={
                        'names': ['french', 'english'],
                        'required': True,
                    },
                    path={'base': 'cfgdir', 'path': 'hello-multi-bfg'},
                    builder=cfg_bfg9000_builder(
                        'hello',
                        usage=cfg_pkg_config_usage(
                            pcfile=None,
                            submodule_map={
                                '*': {'pcfile': {'#phs#': ['hello_', 0]}},
                            }
                        )
                    )
                ),
            ],
        })
