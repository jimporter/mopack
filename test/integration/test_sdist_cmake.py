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
        self.assertPopen(['mopack', 'resolve', config,
                          '-Pprefix=' + self.prefix])
        self.assertExists('mopack/build/greeter/')
        self.assertExists('mopack/logs/greeter.log')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigUsage('greeter')

        include_path = [os.path.join(test_data_dir, 'hello-cmake/include')]
        library_path = [os.path.join(self.pkgbuilddir, 'hello')]
        self.assertPathUsage('hello', include_path=include_path,
                             library_path=library_path, version='1.0')

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(
                common={'deploy_paths': {'prefix': self.prefix}},
                cmake={}, bfg9000={}
            ),
            'packages': [
                cfg_directory_pkg(
                    'hello', config,
                    path={'base': 'cfgdir', 'path': 'hello-cmake'},
                    builder=cfg_cmake_builder('hello'),
                    usage=cfg_path_usage(
                        explicit_version='1.0',
                        compile_flags=[[
                            '-I', {'base': 'srcdir', 'path': ''},
                            '/include'
                        ]],
                        library_path=[{'base': 'builddir', 'path': ''}],
                        libraries=[{'type': 'guess', 'name': 'hello'}]
                    )
                ),
                cfg_directory_pkg(
                    'greeter', config,
                    path={'base': 'cfgdir', 'path': 'greeter-bfg'},
                    builder=cfg_bfg9000_builder('greeter'),
                    usage=cfg_pkg_config_usage(pcname='greeter')
                ),
            ],
        })

        self.assertPopen(['mopack', 'deploy'])
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
        self.assertPopen(['mopack', 'resolve', config,
                          '-Pprefix=' + self.prefix])
        self.assertExists('mopack/build/greeter/')
        self.assertExists('mopack/logs/greeter.log')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        include_path = [os.path.join(test_data_dir, 'greeter-cmake/include')]
        library_path = [os.path.join(self.pkgbuilddir, 'greeter')]
        self.assertPathUsage('greeter', include_path=include_path,
                             library_path=library_path, version='1.0')

        self.assertPkgConfigUsage('hello')

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(
                common={'deploy_paths': {'prefix': self.prefix}},
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
                    builder=cfg_bfg9000_builder('hello'),
                    usage=cfg_pkg_config_usage(pcname='hello')
                ),
                cfg_directory_pkg(
                    'greeter', config,
                    path={'base': 'cfgdir', 'path': 'greeter-cmake'},
                    builder=cfg_cmake_builder('greeter'),
                    usage=cfg_path_usage(
                        explicit_version='1.0',
                        compile_flags=[[
                            '-I', {'base': 'srcdir', 'path': ''},
                            '/include'
                        ]],
                        library_path=[{'base': 'builddir', 'path': ''}],
                        libraries=[{'type': 'guess', 'name': 'greeter'}],
                    )
                ),
            ],
        })

        self.assertPopen(['mopack', 'deploy'])
        include_prefix = '' if platform_name() == 'windows' else 'include/'
        lib_prefix = '' if platform_name() == 'windows' else 'lib/'
        with pushd(self.prefix):
            self.assertExists('include/greeter.hpp')
            self.assertExists(include_prefix + 'hello.hpp')
            self.assertExists(lib_prefix + 'pkgconfig/hello.pc')
