import json
import os

from mopack.platforms import platform_name

from . import *


class TestCleanNeeded(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('sdist')
        self.pkgbuilddir = os.path.join(self.stage, 'mopack', 'build')

    def check_usage(self, name):
        output = json.loads(self.assertPopen([
            'mopack', 'usage', name, '--json'
        ]))
        self.assertEqual(output, {
            'name': name,
            'type': 'pkg-config',
            'path': os.path.join(self.pkgbuilddir, name, 'pkgconfig'),
            'pcfiles': [name],
            'extra_args': [],
        })

    def _options(self):
        return {
            'common': {
                'target_platform': platform_name(),
                'env': AlwaysEqual(),
            },
            'builders': [{
                'type': 'bfg9000',
                'toolchain': None,
            }],
            'sources': [],
        }

    def _builder(self, name, extra_args=[]):
        return {
            'type': 'bfg9000',
            'name': name,
            'extra_args': extra_args,
            'usage': {
                'type': 'pkg-config',
                'path': 'pkgconfig',
                'pcfile': name,
                'extra_args': [],
            },
        }

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-nested-extra.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertExists('mopack/build/greeter/')
        self.assertExists('mopack/build/greeter/extra.txt')
        self.assertExists('mopack/logs/greeter.log')

        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/build/hello/extra.txt')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        self.check_usage('greeter')
        self.check_usage('hello')

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'deploy_paths': {},
            'options': self._options(),
            'packages': [{
                'name': 'hello',
                'config_file': config,
                'source': 'directory',
                'submodules': None,
                'should_deploy': True,
                'builder': self._builder('hello', ['--extra']),
                'path': os.path.join(test_data_dir, 'hello-bfg'),
            }, {
                'name': 'greeter',
                'config_file': config,
                'source': 'directory',
                'submodules': None,
                'should_deploy': True,
                'builder': self._builder('greeter', ['--extra']),
                'path': os.path.join(test_data_dir, 'greeter-bfg'),
            }],
        })

        # Rebuild with a different config.
        config = os.path.join(test_data_dir, 'mopack-nested.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertExists('mopack/build/greeter/')
        self.assertExists('mopack/logs/greeter.log')
        self.assertExists('mopack/src/hello/hello-bfg/')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')
        self.assertNotExists('mopack/build/greeter/extra.txt')
        self.assertNotExists('mopack/build/hello/extra.txt')

        self.check_usage('greeter')
        self.check_usage('hello')

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'deploy_paths': {},
            'options': self._options(),
            'packages': [{
                'name': 'hello',
                'config_file': os.path.join(test_data_dir, 'greeter-bfg',
                                            'mopack.yml'),
                'source': 'tarball',
                'submodules': None,
                'should_deploy': True,
                'builder': self._builder('hello'),
                'url': None,
                'path': os.path.join(test_data_dir, 'hello-bfg.tar.gz'),
                'files': [],
                'srcdir': None,
                'guessed_srcdir': 'hello-bfg',
                'patch': None,
            }, {
                'name': 'greeter',
                'config_file': config,
                'source': 'directory',
                'submodules': None,
                'should_deploy': True,
                'builder': self._builder('greeter'),
                'path': os.path.join(test_data_dir, 'greeter-bfg'),
            }],
        })
