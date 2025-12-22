import json
import os

from . import *


class TestLocal(IntegrationTest):
    name = 'local'

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'local')
        self.assertPopen(mopack_cmd('resolve', config))
        self.assertExists('mopack/logs/conan.log')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigLinkage(
            'zlib', pkg_config_path=[
                os.path.join(self.stage, 'mopack', 'conan'),
            ], version='1.2.13', include_path=mock.ANY, library_path=mock.ANY,
            libraries=['zdll' if platform_name() == 'windows' else 'z']
        )

        self.assertOutput(['mopack', 'list-files'], (
            os.path.join(config, 'mopack.yml') + '\n' +
            os.path.join(config, 'mopack-local.yml') + '\n'
        ))
        output = json.loads(self.assertPopen(
            mopack_cmd('list-files', '--json')
        ))
        self.assertEqual(output, [os.path.join(config, 'mopack.yml'),
                                  os.path.join(config, 'mopack-local.yml')])

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(
                conan={'build': ['missing']}
            ),
            'packages': [
                cfg_conan_pkg(
                    'zlib', os.path.join(config, 'mopack-local.yml'),
                    remote='zlib/1.2.13',
                    options={'shared': True},
                    linkage=cfg_pkg_config_linkage(
                        pcname='zlib',
                        pkg_config_path=[{'base': 'builddir', 'path': ''}]
                    )
                )
            ],
        })
