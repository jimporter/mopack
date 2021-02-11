import json
import os

from mopack.platforms import platform_name

from . import *


class TestInterpolation(IntegrationTest):
    name = 'interpolation'

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

    def test_resolve_enabled(self):
        config = os.path.join(test_data_dir, 'mopack-interpolation.yml')
        self.assertPopen(['mopack', 'resolve', config],
                         extra_env={'MOPACK_TEST_EXTRA': '1'})
        self.assertNotExists('mopack/src/hello/hello-bfg/build.bfg')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

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
                'builder': self._builder('hello', extra_args=['--extra']),
                'path': {'base': 'cfgdir', 'path': 'hello-bfg'},
            }],
        })

    def test_resolve_disabled(self):
        config = os.path.join(test_data_dir, 'mopack-interpolation.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertNotExists('mopack/src/hello/hello-bfg/build.bfg')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

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
                'builder': self._builder('hello'),
                'path': {'base': 'cfgdir', 'path': 'hello-bfg'},
            }],
        })
