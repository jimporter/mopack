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
        self.assertExists('mopack/src/foo/bfg_project/build.bfg')
        self.assertExists('mopack/build/foo/')
        self.assertExists('mopack/foo.log')
        self.assertExists('mopack/mopack.json')

        output = json.loads(self.assertPopen([
            'mopack', 'usage', 'foo', '--json'
        ]))
        self.assertEqual(output, {
            'name': 'foo',
            'type': 'pkg-config',
            'path': os.path.join(self.stage, 'mopack', 'build', 'foo',
                                 'pkgconfig'),
        })

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'deploy_paths': {'prefix': self.prefix},
            'options': [],
            'packages': [{
                'config': {
                    'name': 'foo',
                    'config_file': config,
                    'source': 'tarball',
                    'builder': {
                        'type': 'bfg9000',
                        'name': 'foo',
                        'extra_args': [],
                        'usage': {
                            'type': 'pkg-config',
                            'path': 'pkgconfig',
                        },
                    },
                    'url': None,
                    'path': os.path.join(test_data_dir, 'bfg_project.tar.gz'),
                    'files': None,
                    'srcdir': None,
                    'guessed_srcdir': 'bfg_project',
                },
                'usage': {
                    'type': 'pkg-config',
                    'path': os.path.join(self.stage, 'mopack', 'build', 'foo',
                                         'pkgconfig'),
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
        self.assertNotExists('mopack/src/foo/bfg_project/build.bfg')
        self.assertExists('mopack/build/foo/')
        self.assertExists('mopack/foo.log')
        self.assertExists('mopack/mopack.json')

        output = json.loads(self.assertPopen([
            'mopack', 'usage', 'foo', '--json'
        ]))
        self.assertEqual(output, {
            'name': 'foo',
            'type': 'pkg-config',
            'path': os.path.join(self.stage, 'mopack', 'build', 'foo',
                                 'pkgconfig'),
        })

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'deploy_paths': {},
            'options': [],
            'packages': [{
                'config': {
                    'name': 'foo',
                    'config_file': config,
                    'source': 'directory',
                    'builder': {
                        'type': 'bfg9000',
                        'name': 'foo',
                        'extra_args': [],
                        'usage': {
                            'type': 'pkg-config',
                            'path': 'pkgconfig',
                        },
                    },
                    'path': os.path.join(test_data_dir, 'bfg_project'),
                },
                'usage': {
                    'type': 'pkg-config',
                    'path': os.path.join(self.stage, 'mopack', 'build', 'foo',
                                         'pkgconfig'),
                },
            }],
        })
