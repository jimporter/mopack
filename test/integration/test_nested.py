import json
import os

from . import *


class TestNested(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('nested')

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-nested.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertExists('mopack/build/greeter/')
        self.assertExists('mopack/greeter.log')
        self.assertExists('mopack/src/bfg_project/build.bfg')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/hello.log')
        self.assertExists('mopack/mopack.json')

        output = json.loads(self.assertPopen(['mopack', 'info', 'greeter']))
        self.assertEqual(output, {
            'usage': 'pkgconfig',
            'path': os.path.join(self.stage, 'mopack', 'build', 'greeter',
                                 'pkgconfig'),
        })

        output = json.loads(self.assertPopen(['mopack', 'info', 'hello']))
        self.assertEqual(output, {
            'usage': 'pkgconfig',
            'path': os.path.join(self.stage, 'mopack', 'build', 'hello',
                                 'pkgconfig'),
        })
