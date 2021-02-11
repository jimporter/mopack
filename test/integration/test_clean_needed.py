import json
import os

from mopack.platforms import platform_name

from . import *


class TestCleanNeeded(IntegrationTest):
    name = 'clean-needed'

    def _options(self):
        return {
            'common': {
                '_version': 1,
                'target_platform': platform_name(),
                'env': AlwaysEqual(),
                'deploy_paths': {},
            },
            'builders': [{
                'type': 'bfg9000',
                '_version': 1,
                'toolchain': None,
            }],
            'sources': [],
        }

    def _builder(self, name, extra_args=[]):
        return {
            'type': 'bfg9000',
            '_version': 1,
            'name': name,
            'extra_args': extra_args,
            'usage': {
                'type': 'pkg-config',
                '_version': 1,
                'path': {'base': 'builddir', 'path': 'pkgconfig'},
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

        self.assertPkgConfigUsage('greeter')
        self.assertPkgConfigUsage('hello')

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': self._options(),
            'packages': [{
                'name': 'hello',
                'config_file': config,
                'resolved': True,
                'source': 'directory',
                '_version': 1,
                'submodules': None,
                'should_deploy': True,
                'builder': self._builder('hello', ['--extra']),
                'path': {'base': 'cfgdir', 'path': 'hello-bfg'},
            }, {
                'name': 'greeter',
                'config_file': config,
                'resolved': True,
                'source': 'directory',
                '_version': 1,
                'submodules': None,
                'should_deploy': True,
                'builder': self._builder('greeter', ['--extra']),
                'path': {'base': 'cfgdir', 'path': 'greeter-bfg'},
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

        self.assertPkgConfigUsage('greeter')
        self.assertPkgConfigUsage('hello')

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': self._options(),
            'packages': [{
                'name': 'hello',
                'config_file': os.path.join(test_data_dir, 'greeter-bfg',
                                            'mopack.yml'),
                'resolved': True,
                'source': 'tarball',
                '_version': 1,
                'submodules': None,
                'should_deploy': True,
                'builder': self._builder('hello'),
                'url': None,
                'path': {'base': 'cfgdir',
                         'path': os.path.join('..', 'hello-bfg.tar.gz')},
                'files': [],
                'srcdir': None,
                'guessed_srcdir': 'hello-bfg',
                'patch': None,
            }, {
                'name': 'greeter',
                'config_file': config,
                'resolved': True,
                'source': 'directory',
                '_version': 1,
                'submodules': None,
                'should_deploy': True,
                'builder': self._builder('greeter'),
                'path': {'base': 'cfgdir', 'path': 'greeter-bfg'},
            }],
        })
