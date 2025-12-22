import json
import os

from mopack.path import pushd
from mopack.platforms import platform_name

from . import *


class TestCustomBuilder(IntegrationTest):
    name = 'custom-builder'

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-custom-builder.yml')
        self.assertPopen(mopack_cmd('resolve', config))
        self.assertExists('mopack/src/hello/hello-bfg/build.bfg')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigLinkage('hello', include_path=[
            os.path.join(self.pkgsrcdir, 'hello', 'hello-bfg', 'include'),
        ])

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(),
            'packages': [
                cfg_tarball_pkg(
                    'hello', config,
                    path={'base': 'cfgdir', 'path': 'hello-bfg.tar.gz'},
                    guessed_srcdir='hello-bfg',
                    builders=[cfg_custom_builder(
                        build_commands=[
                            ['bfg9000', 'configure',
                             [{'base': 'builddir', 'path': ''}]],
                            ['cd', [{'base': 'builddir', 'path': ''}, '/.']],
                            ['ninja'],
                        ],
                        deploy_commands=[
                            ['ninja', 'install'],
                        ]
                    )],
                    linkage=cfg_pkg_config_linkage(pcname='hello')
                ),
            ],
        })


class TestCustomBuilderDeploy(IntegrationTest):
    name = 'custom-builder-deploy'
    deploy = True

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-custom-builder.yml')
        self.assertPopen(mopack_cmd(
            'resolve', config, '-dprefix=' + self.prefix
        ))
        self.assertExists('mopack/src/hello/hello-bfg/build.bfg')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigLinkage('hello', include_path=[
            os.path.join(self.pkgsrcdir, 'hello', 'hello-bfg', 'include'),
        ])

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(
                common={'deploy_dirs': {'prefix': self.prefix}}
            ),
            'packages': [
                cfg_tarball_pkg(
                    'hello', config,
                    path={'base': 'cfgdir', 'path': 'hello-bfg.tar.gz'},
                    guessed_srcdir='hello-bfg',
                    builders=[cfg_custom_builder(
                        build_commands=[
                            ['bfg9000', 'configure',
                             [{'base': 'builddir', 'path': ''}],
                             ['--prefix=', {'base': 'absolute',
                                            'path': self.prefix}]],
                            ['cd', [{'base': 'builddir', 'path': ''}, '/.']],
                            ['ninja'],
                        ],
                        deploy_commands=[
                            ['ninja', 'install'],
                        ]
                    )],
                    linkage=cfg_pkg_config_linkage(pcname='hello')
                ),
            ],
        })

        self.assertPopen(mopack_cmd('--debug', 'deploy'))
        include_prefix = '' if platform_name() == 'windows' else 'include/'
        lib_prefix = '' if platform_name() == 'windows' else 'lib/'
        with pushd(self.prefix):
            self.assertExists(include_prefix + 'hello.hpp')
            self.assertExists(lib_prefix + 'pkgconfig/hello.pc')
