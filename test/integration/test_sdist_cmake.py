import json
import os

from mopack.path import pushd
from mopack.platforms import platform_name

from . import *


class TestInnerCMake(IntegrationTest):
    name = 'inner-cmake'
    deploy = True

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-inner-cmake.yml')
        self.assertPopen(mopack_cmd(
            'resolve', config, '-dprefix=' + self.prefix
        ))
        self.assertExists('mopack/build/greeter/')
        self.assertExists('mopack/logs/greeter.log')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigLinkage('greeter')

        include_path = [os.path.join(test_data_dir, 'hello-cmake', 'include')]
        library_path = [os.path.join(self.pkgbuilddir, 'hello')]
        self.assertPathLinkage('hello', include_path=include_path,
                               library_path=library_path, version='1.0')

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(
                common={'deploy_dirs': {'prefix': self.prefix}},
                cmake={}, bfg9000={}
            ),
            'packages': [
                cfg_directory_pkg(
                    'hello', config,
                    path={'base': 'cfgdir', 'path': 'hello-cmake'},
                    builders=[cfg_cmake_builder()],
                    linkage=cfg_path_linkage(
                        explicit_version='1.0',
                        compile_flags=[[
                            '-I', {'base': 'srcdir', 'path': ''},
                            '/include'
                        ]],
                        library_path=[{'base': 'builddir', 'path': ''}],
                        libraries=['hello']
                    )
                ),
                cfg_directory_pkg(
                    'greeter', config,
                    path={'base': 'cfgdir', 'path': 'greeter-bfg'},
                    builders=[cfg_bfg9000_builder()],
                    linkage=cfg_pkg_config_linkage(pcname='greeter')
                ),
            ],
        })

        self.assertPopen(mopack_cmd('deploy'))
        include_prefix = '' if platform_name() == 'windows' else 'include/'
        lib_prefix = '' if platform_name() == 'windows' else 'lib/'
        with pushd(self.prefix):
            self.assertExists(include_prefix + 'greeter.hpp')
            self.assertExists(lib_prefix + 'pkgconfig/greeter.pc')
            self.assertExists('include/hello.hpp')


class TestOuterCMake(IntegrationTest):
    name = 'outer-cmake'
    deploy = True

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-outer-cmake.yml')
        self.assertPopen(mopack_cmd(
            'resolve', config, '-dprefix=' + self.prefix
        ))
        self.assertExists('mopack/build/greeter/')
        self.assertExists('mopack/logs/greeter.log')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        include_path = [os.path.join(test_data_dir, 'greeter-cmake',
                                     'include')]
        library_path = [os.path.join(self.pkgbuilddir, 'greeter')]
        self.assertPathLinkage('greeter', include_path=include_path,
                               library_path=library_path, version='1.0')

        self.assertPkgConfigLinkage('hello')

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(
                common={'deploy_dirs': {'prefix': self.prefix}},
                bfg9000={}, cmake={}
            ),
            'packages': [
                cfg_tarball_pkg(
                    'hello',
                    os.path.join(test_data_dir, 'greeter-cmake', 'mopack.yml'),
                    parent='greeter',
                    path={'base': 'cfgdir',
                          'path': os.path.join('..', 'hello-bfg.tar.gz')},
                    guessed_srcdir='hello-bfg',
                    builders=[cfg_bfg9000_builder()],
                    linkage=cfg_pkg_config_linkage(pcname='hello')
                ),
                cfg_directory_pkg(
                    'greeter', config,
                    path={'base': 'cfgdir', 'path': 'greeter-cmake'},
                    builders=[cfg_cmake_builder()],
                    linkage=cfg_path_linkage(
                        explicit_version='1.0',
                        compile_flags=[[
                            '-I', {'base': 'srcdir', 'path': ''},
                            '/include'
                        ]],
                        library_path=[{'base': 'builddir', 'path': ''}],
                        libraries=['greeter'],
                    )
                ),
            ],
        })

        self.assertPopen(mopack_cmd('deploy'))
        include_prefix = '' if platform_name() == 'windows' else 'include/'
        lib_prefix = '' if platform_name() == 'windows' else 'lib/'
        with pushd(self.prefix):
            self.assertExists('include/greeter.hpp')
            self.assertExists(include_prefix + 'hello.hpp')
            self.assertExists(lib_prefix + 'pkgconfig/hello.pc')
