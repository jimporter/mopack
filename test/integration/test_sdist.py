import json
import os

from . import *


class TestSdist(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('sdist')

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-tarball.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertExists('mopack/src/bfg_project/build.bfg')
        self.assertExists('mopack/build/foo/')
        self.assertExists('mopack/foo.log')
        self.assertExists('mopack/mopack.json')

        output = json.loads(self.assertPopen(['mopack', 'info', 'foo']))
        self.assertEqual(output, {
            'config': {
                'source': 'tarball',
                'name': 'foo',
                'config_file': config,
                'builder': {
                    'type': 'bfg9000',
                    'name': 'foo',
                    'builddir': 'foo',
                    'extra_args': [],
                },
                'url': None,
                'path': os.path.join(test_data_dir, 'bfg_project.tar.gz'),
                'files': None,
                'srcdir': None,
                'guessed_srcdir': 'bfg_project',
            },
            'usage': {
                'type': 'pkgconfig',
                'path': os.path.join(self.stage, 'mopack', 'build', 'foo',
                                     'pkgconfig'),
            }
        })
