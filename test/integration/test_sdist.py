import json
import os

from mopack.path import pushd

from . import *


class TestTarball(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('tarball')
        self.prefix = stage_dir('tarball-install', chdir=False)

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-tarball.yml')
        self.assertPopen(['mopack', 'resolve', config,
                          '-Pprefix=' + self.prefix])
        self.assertExists('mopack/src/hello/hello-bfg/build.bfg')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/hello.log')
        self.assertExists('mopack/mopack.json')

        output = json.loads(self.assertPopen([
            'mopack', 'usage', 'hello', '--json'
        ]))
        self.assertEqual(output, {
            'name': 'hello',
            'type': 'pkg-config',
            'path': os.path.join(self.stage, 'mopack', 'build', 'hello',
                                 'pkgconfig'),
        })

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'deploy_paths': {'prefix': self.prefix},
            'options': {
                'general': {'target_platform': None},
                'builders': [{
                    'type': 'bfg9000',
                    'toolchain': None,
                }],
                'sources': [],
            },
            'packages': [{
                'config': {
                    'name': 'hello',
                    'config_file': config,
                    'source': 'tarball',
                    'builder': {
                        'type': 'bfg9000',
                        'name': 'hello',
                        'extra_args': [],
                        'usage': {
                            'type': 'pkg-config',
                            'path': 'pkgconfig',
                        },
                    },
                    'url': None,
                    'path': os.path.join(test_data_dir, 'hello-bfg.tar.gz'),
                    'files': None,
                    'srcdir': None,
                    'guessed_srcdir': 'hello-bfg',
                },
                'usage': {
                    'type': 'pkg-config',
                    'path': os.path.join(self.stage, 'mopack', 'build',
                                         'hello', 'pkgconfig'),
                },
            }],
        })

        self.assertPopen(['mopack', 'deploy'])
        with pushd(self.prefix):
            self.assertExists('include/hello.hpp')
            self.assertExists('lib/pkgconfig/hello.pc')


class TestDirectory(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('directory')

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-directory-implicit.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertNotExists('mopack/src/hello/hello-bfg/build.bfg')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/hello.log')
        self.assertExists('mopack/mopack.json')

        output = json.loads(self.assertPopen([
            'mopack', 'usage', 'hello', '--json'
        ]))
        self.assertEqual(output, {
            'name': 'hello',
            'type': 'pkg-config',
            'path': os.path.join(self.stage, 'mopack', 'build', 'hello',
                                 'pkgconfig'),
        })

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'deploy_paths': {},
            'options': {
                'general': {'target_platform': None},
                'builders': [{
                    'type': 'bfg9000',
                    'toolchain': None,
                }],
                'sources': [],
            },
            'packages': [{
                'config': {
                    'name': 'hello',
                    'config_file': config,
                    'source': 'directory',
                    'builder': {
                        'type': 'bfg9000',
                        'name': 'hello',
                        'extra_args': [],
                        'usage': {
                            'type': 'pkg-config',
                            'path': 'pkgconfig',
                        },
                    },
                    'path': os.path.join(test_data_dir, 'hello-bfg'),
                },
                'usage': {
                    'type': 'pkg-config',
                    'path': os.path.join(self.stage, 'mopack', 'build',
                                         'hello', 'pkgconfig'),
                },
            }],
        })
