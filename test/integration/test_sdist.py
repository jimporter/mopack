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
            'source': 'tarball',
            'usage': {
                'type': 'pkgconfig',
                'path': os.path.join(self.stage, 'mopack', 'build', 'foo',
                                     'pkgconfig'),
            }
        })
