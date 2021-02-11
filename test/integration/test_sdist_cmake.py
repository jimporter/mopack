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

        include_path = [os.path.join(test_data_dir, 'hello-cmake', 'include')]
        library_path = [os.path.join(self.pkgbuilddir, 'hello')]
        self.assertPathUsage('hello', include_path=include_path,
                             library_path=library_path)

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': {
                'common': {
                    '_version': 1,
                    'target_platform': platform_name(),
                    'env': AlwaysEqual(),
                    'deploy_paths': {'prefix': self.prefix},
                },
                'builders': [
                    {'type': 'cmake', '_version': 1, 'toolchain': None},
                    {'type': 'bfg9000', '_version': 1, 'toolchain': None},
                ],
                'sources': [],
            },
            'packages': [{
                'name': 'hello',
                'config_file': config,
                'resolved': True,
                'source': 'directory',
                '_version': 1,
                'submodules': None,
                'should_deploy': True,
                'builder': {
                    'type': 'cmake',
                    '_version': 1,
                    'name': 'hello',
                    'extra_args': [],
                    'usage': {
                        'type': 'path',
                        '_version': 1,
                        'auto_link': False,
                        'include_path': [{'base': 'srcdir',
                                          'path': 'include'}],
                        'library_path': [{'base': 'builddir', 'path': ''}],
                        'headers': [],
                        'libraries': [{'type': 'guess', 'name': 'hello'}],
                        'compile_flags': [],
                        'link_flags': [],
                    },
                },
                'path': {'base': 'cfgdir', 'path': 'hello-cmake'},
            }, {
                'name': 'greeter',
                'config_file': config,
                'resolved': True,
                'source': 'directory',
                '_version': 1,
                'submodules': None,
                'should_deploy': True,
                'builder': {
                    'type': 'bfg9000',
                    '_version': 1,
                    'name': 'greeter',
                    'extra_args': [],
                    'usage': {
                        'type': 'pkg-config',
                        '_version': 1,
                        'path': {'base': 'builddir', 'path': 'pkgconfig'},
                        'pcfile': 'greeter',
                        'extra_args': [],
                    },
                },
                'path': {'base': 'cfgdir', 'path': 'greeter-bfg'},
            }],
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

        include_path = [os.path.join(test_data_dir, 'greeter-cmake',
                                     'include')]
        library_path = [os.path.join(self.pkgbuilddir, 'greeter')]
        self.assertPathUsage('greeter', include_path=include_path,
                             library_path=library_path)

        self.assertPkgConfigUsage('hello')

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': {
                'common': {
                    '_version': 1,
                    'target_platform': platform_name(),
                    'env': AlwaysEqual(),
                    'deploy_paths': {'prefix': self.prefix},
                },
                'builders': [
                    {'type': 'bfg9000', '_version': 1, 'toolchain': None},
                    {'type': 'cmake', '_version': 1, 'toolchain': None},
                ],
                'sources': [],
            },
            'packages': [{
                'name': 'hello',
                'config_file': os.path.join(test_data_dir, 'greeter-cmake',
                                            'mopack.yml'),
                'resolved': True,
                'source': 'tarball',
                '_version': 1,
                'submodules': None,
                'should_deploy': True,
                'builder': {
                    'type': 'bfg9000',
                    '_version': 1,
                    'name': 'hello',
                    'extra_args': [],
                    'usage': {
                        'type': 'pkg-config',
                        '_version': 1,
                        'path': {'base': 'builddir', 'path': 'pkgconfig'},
                        'pcfile': 'hello',
                        'extra_args': [],
                    },
                },
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
                '_version': 1,
                'submodules': None,
                'should_deploy': True,
                'builder': {
                    'type': 'cmake',
                    '_version': 1,
                    'name': 'greeter',
                    'extra_args': [],
                    'usage': {
                        'type': 'path',
                        '_version': 1,
                        'auto_link': False,
                        'include_path': [{'base': 'srcdir',
                                          'path': 'include'}],
                        'library_path': [{'base': 'builddir', 'path': ''}],
                        'headers': [],
                        'libraries': [{'type': 'guess', 'name': 'greeter'}],
                        'compile_flags': [],
                        'link_flags': [],
                    },
                },
                'path': {'base': 'cfgdir', 'path': 'greeter-cmake'},
            }],
        })

        self.assertPopen(['mopack', 'deploy'])
        include_prefix = '' if platform_name() == 'windows' else 'include/'
        lib_prefix = '' if platform_name() == 'windows' else 'lib/'
        with pushd(self.prefix):
            self.assertExists('include/greeter.hpp')
            self.assertExists(include_prefix + 'hello.hpp')
            self.assertExists(lib_prefix + 'pkgconfig/hello.pc')
