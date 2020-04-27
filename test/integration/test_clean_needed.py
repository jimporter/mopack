import json
import os

from . import *


class TestCleanNeeded(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('sdist')
        self.pkgbuilddir = os.path.join(self.stage, 'mopack', 'build')

    def _builder(self, name, extra_args=[]):
        return {
            'type': 'bfg9000',
            'name': name,
            'extra_args': extra_args,
            'usage': {
                'type': 'pkg-config',
                'path': 'pkgconfig',
            },
        }

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-nested-extra.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertExists('mopack/build/greeter/')
        self.assertExists('mopack/build/greeter/extra.txt')
        self.assertExists('mopack/greeter.log')

        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/build/hello/extra.txt')
        self.assertExists('mopack/hello.log')
        self.assertExists('mopack/mopack.json')

        output = json.loads(self.assertPopen([
            'mopack', 'usage', 'greeter', '--json'
        ]))
        self.assertEqual(output, {
            'name': 'greeter',
            'type': 'pkg-config',
            'path': os.path.join(self.pkgbuilddir, 'greeter', 'pkgconfig'),
        })

        output = json.loads(self.assertPopen([
            'mopack', 'usage', 'hello', '--json'
        ]))
        self.assertEqual(output, {
            'name': 'hello',
            'type': 'pkg-config',
            'path': os.path.join(self.pkgbuilddir, 'hello', 'pkgconfig'),
        })

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'deploy_paths': {},
            'options': [],
            'packages': [{
                'config': {
                    'name': 'hello',
                    'config_file': config,
                    'source': 'directory',
                    'builder': self._builder('hello', ['--extra']),
                    'path': os.path.join(test_data_dir, 'bfg_project'),
                },
                'usage': {
                    'type': 'pkg-config',
                    'path': os.path.join(self.pkgbuilddir, 'hello',
                                         'pkgconfig'),
                },
            }, {
                'config': {
                    'name': 'greeter',
                    'config_file': config,
                    'source': 'directory',
                    'builder': self._builder('greeter', ['--extra']),
                    'path': os.path.join(test_data_dir, 'nested'),
                },
                'usage': {
                    'type': 'pkg-config',
                    'path': os.path.join(self.pkgbuilddir, 'greeter',
                                         'pkgconfig'),
                },
            }],
        })

        # Rebuild with a different config.
        config = os.path.join(test_data_dir, 'mopack-nested.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertExists('mopack/build/greeter/')
        self.assertExists('mopack/greeter.log')
        self.assertExists('mopack/src/hello/bfg_project/')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/hello.log')
        self.assertExists('mopack/mopack.json')
        self.assertNotExists('mopack/build/greeter/extra.txt')
        self.assertNotExists('mopack/build/hello/extra.txt')

        output = json.loads(self.assertPopen([
            'mopack', 'usage', 'greeter', '--json'
        ]))
        self.assertEqual(output, {
            'name': 'greeter',
            'type': 'pkg-config',
            'path': os.path.join(self.pkgbuilddir, 'greeter', 'pkgconfig'),
        })

        output = json.loads(self.assertPopen([
            'mopack', 'usage', 'hello', '--json'
        ]))
        self.assertEqual(output, {
            'name': 'hello',
            'type': 'pkg-config',
            'path': os.path.join(self.pkgbuilddir, 'hello', 'pkgconfig'),
        })

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'deploy_paths': {},
            'options': [],
            'packages': [{
                'config': {
                    'name': 'hello',
                    'config_file': os.path.join(test_data_dir, 'nested',
                                                'mopack.yml'),
                    'source': 'tarball',
                    'builder': self._builder('hello'),
                    'url': None,
                    'path': os.path.join(test_data_dir, 'bfg_project.tar.gz'),
                    'files': None,
                    'srcdir': None,
                    'guessed_srcdir': 'bfg_project',
                },
                'usage': {
                    'type': 'pkg-config',
                    'path': os.path.join(self.pkgbuilddir, 'hello',
                                         'pkgconfig'),
                },
            }, {
                'config': {
                    'name': 'greeter',
                    'config_file': config,
                    'source': 'directory',
                    'builder': self._builder('greeter'),
                    'path': os.path.join(test_data_dir, 'nested'),
                },
                'usage': {
                    'type': 'pkg-config',
                    'path': os.path.join(self.pkgbuilddir, 'greeter',
                                         'pkgconfig'),
                },
            }],
        })
