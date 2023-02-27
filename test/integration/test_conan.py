import json
import os

from . import *


class TestConan(IntegrationTest):
    name = 'conan'

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-conan.yml')
        self.assertPopen(['mopack', 'resolve',
                          '-Oconan:extra_args=-gCMakeDeps', config])
        self.assertExists('mopack/logs/conan.log')
        self.assertExists('mopack/conan/conanfile.txt')
        self.assertExists('mopack/conan/zlib.pc')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigUsage('zlib', pkg_config_path=[os.path.join(
            self.stage, 'mopack', 'conan'
        )])

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(
                conan={'build': ['missing'], 'extra_args': ['-gCMakeDeps']}
            ),
            'packages': [
                cfg_conan_pkg(
                    'zlib', config,
                    remote='zlib/1.2.13',
                    options={'shared': True},
                    usage=cfg_pkg_config_usage(
                        pcname='zlib',
                        pkg_config_path=[{'base': 'builddir', 'path': ''}]
                    )
                ),
            ],
        })
