import json
import os

from mopack.platforms import platform_name

from . import *


class TestConditional(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('conditional')

    def check_usage(self, name):
        output = json.loads(self.assertPopen([
            'mopack', 'usage', name, '--json'
        ]))
        self.assertEqual(output, {
            'name': name,
            'type': 'pkg-config',
            'path': os.path.join(self.stage, 'mopack', 'build', name,
                                 'pkgconfig'),
            'pcfiles': [name],
            'extra_args': [],
        })

    def _options(self):
        return {
            'common': {
                'target_platform': platform_name(),
                'env': AlwaysEqual(),
                'deploy_paths': {},
            },
            'builders': [{
                'type': 'bfg9000',
                'toolchain': None,
            }],
            'sources': [],
        }

    def _builder(self, name):
        return {
            'type': 'bfg9000',
            'name': name,
            'extra_args': [],
            'usage': {
                'type': 'pkg-config',
                'path': {'base': 'builddir', 'path': 'pkgconfig'},
                'pcfile': name,
                'extra_args': [],
            },
        }

    def test_resolve(self):
        want_tarball = platform_name() == 'windows'

        config = os.path.join(test_data_dir, 'mopack-conditional.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertExistence('mopack/src/hello/hello-bfg/build.bfg',
                             want_tarball)
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        self.check_usage('hello')

        output = json.loads(slurp('mopack/mopack.json'))
        if want_tarball:
            hellopkg = {
                'name': 'hello',
                'config_file': config,
                'resolved': True,
                'source': 'tarball',
                'submodules': None,
                'should_deploy': True,
                'builder': self._builder('hello'),
                'url': None,
                'path': {'base': 'cfgdir', 'path': 'hello-bfg.tar.gz'},
                'files': [],
                'srcdir': None,
                'guessed_srcdir': 'hello-bfg',
                'patch': None,
            }
        else:
            hellopkg = {
                'name': 'hello',
                'config_file': config,
                'resolved': True,
                'source': 'directory',
                'submodules': None,
                'should_deploy': True,
                'builder': self._builder('hello'),
                'path': {'base': 'cfgdir', 'path': 'hello-bfg'},
            }
        self.assertEqual(output['metadata'], {
            'options': self._options(),
            'packages': [hellopkg],
        })
