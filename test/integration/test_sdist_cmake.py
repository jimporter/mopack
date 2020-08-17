import json
import os

from mopack.path import pushd
from mopack.platforms import platform_name

from . import *


class TestNestedCMake(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('nested-cmake')
        self.prefix = stage_dir('nested-cmake-install', chdir=False)
        self.pkgbuilddir = os.path.join(self.stage, 'mopack', 'build')

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-nested-cmake.yml')
        self.assertPopen(['mopack', 'resolve', config,
                          '-Pprefix=' + self.prefix])
        self.assertExists('mopack/build/greeter/')
        self.assertExists('mopack/greeter.log')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/hello.log')
        self.assertExists('mopack/mopack.json')

        output = json.loads(self.assertPopen([
            'mopack', 'usage', 'greeter', '--json'
        ]))
        self.assertEqual(output, {
            'name': 'greeter',
            'type': 'pkg-config',
            'path': os.path.join(self.pkgbuilddir, 'greeter', 'pkgconfig'),
            'pcfiles': ['greeter'],
            'extra_args': [],
        })

        output = json.loads(self.assertPopen([
            'mopack', 'usage', 'hello', '--json'
        ]))
        self.assertEqual(output, {
            'name': 'hello',
            'type': 'path',
            'auto_link': False,
            'include_path': [os.path.join(test_data_dir, 'hello-cmake',
                                          'include')],
            'library_path': [os.path.join(self.pkgbuilddir, 'hello')],
            'headers': [],
            'libraries': ['hello'],
            'compile_flags': [],
            'link_flags': [],
        })

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'deploy_paths': {'prefix': self.prefix},
            'options': {
                'common': {
                    'target_platform': platform_name(),
                    'env': AlwaysEqual(),
                },
                'builders': [{
                    'type': 'bfg9000',
                    'toolchain': None,
                }],
                'sources': [],
            },
            'packages': [{
                'name': 'hello',
                'config_file': config,
                'source': 'directory',
                'submodules': None,
                'builder': {
                    'type': 'cmake',
                    'name': 'hello',
                    'extra_args': [],
                    'usage': {
                        'type': 'path',
                        'auto_link': False,
                        'include_path': ['include'],
                        'library_path': ['.'],
                        'headers': [],
                        'libraries': [{'type': 'guess', 'name': 'hello'}],
                        'compile_flags': [],
                        'link_flags': [],
                    },
                },
                'path': os.path.join(test_data_dir, 'hello-cmake'),
            }, {
                'name': 'greeter',
                'config_file': config,
                'source': 'directory',
                'submodules': None,
                'builder': {
                    'type': 'bfg9000',
                    'name': 'greeter',
                    'extra_args': [],
                    'usage': {
                        'type': 'pkg-config',
                        'path': 'pkgconfig',
                        'pcfile': 'greeter',
                        'extra_args': [],
                    },
                },
                'path': os.path.join(test_data_dir, 'greeter-bfg'),
            }],
        })

        self.assertPopen(['mopack', 'deploy'])
        include_prefix = '' if platform_name() == 'windows' else 'include/'
        lib_prefix = '' if platform_name() == 'windows' else 'lib/'
        with pushd(self.prefix):
            self.assertExists(include_prefix + 'greeter.hpp')
            self.assertExists(lib_prefix + 'pkgconfig/greeter.pc')
            self.assertExists('include/hello.hpp')
