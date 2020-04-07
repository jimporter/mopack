import json
import os

from . import *


class TestSdist(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('sdist')

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-tarball.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertExists('mopack/bfg_project/build.bfg')
        self.assertExists('mopack/bfg_project/build/')
        self.assertExists('mopack/foo.log')
        self.assertExists('mopack/mopack.json')

        output = json.loads(self.assertPopen(['mopack', 'info', 'foo']))
        self.assertEqual(output, {
            'usage': 'pkgconfig',
            'path': os.path.join(self.stage, 'mopack', 'bfg_project', 'build',
                                 'pkgconfig'),
        })
