import json
import os

from mopack.platforms import platform_name

from . import *


class TestSubmodules(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('submodules')

    def check_usage(self, submodules):
        output = json.loads(self.assertPopen(
            ['mopack', 'usage', 'hello'] + ['-s' + i for i in submodules] +
            ['--json']
        ))
        self.assertEqual(output, {
            'name': 'hello',
            'type': 'pkg-config',
            'path': os.path.join(self.stage, 'mopack', 'build', 'hello',
                                 'pkgconfig'),
            'pcfiles': ['hello_' + i for i in submodules],
            'extra_args': [],
        })

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-submodules-implicit.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertNotExists('mopack/src/hello/hello-bfg/build.bfg')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/hello.log')
        self.assertExists('mopack/mopack.json')

        self.check_usage(['french'])
        self.check_usage(['english'])
        self.check_usage(['french', 'english'])

        self.assertPopen(['mopack', 'usage', 'hello', '--json'],
                         returncode=1)

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'deploy_paths': {},
            'options': {
                'common': {'target_platform': platform_name()},
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
                'submodules': {
                    'names': ['french', 'english'],
                    'required': True,
                },
                'builder': {
                    'type': 'bfg9000',
                    'name': 'hello',
                    'extra_args': [],
                    'usage': {
                        'type': 'pkg-config',
                        'path': 'pkgconfig',
                        'pcfile': None,
                        'extra_args': [],
                        'submodule_map': {
                            '*': {'pcfile': 'hello_{submodule}'},
                        },
                    },
                },
                'path': os.path.join(test_data_dir, 'hello-multi-bfg'),
            }],
        })
