import json
import os

from mopack.path import pushd
from mopack.platforms import platform_name

from . import *


class CommonTest(IntegrationTest):
    def _options(self, deploy_paths={}):
        return {
            'common': {
                '_version': 1,
                'target_platform': platform_name(),
                'env': AlwaysEqual(),
                'deploy_paths': deploy_paths,
            },
            'builders': [{
                'type': 'bfg9000',
                '_version': 1,
                'toolchain': None,
            }],
            'sources': [],
        }

    def _builder(self, name):
        return {
            'type': 'bfg9000',
            '_version': 1,
            'name': name,
            'extra_args': [],
            'usage': {
                'type': 'pkg-config',
                '_version': 1,
                'path': {'base': 'builddir', 'path': 'pkgconfig'},
                'pcfile': name,
                'extra_args': [],
            },
        }


class TestBroken(CommonTest):
    name = 'broken'
    deploy = True

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-broken.yml')
        self.assertPopen(['mopack', 'resolve', config,
                          '-Pprefix=' + self.prefix], returncode=1)
        self.assertExists('mopack/src/hello/hello-bfg/build.bfg')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')
        self.assertNotExists('mopack/build/hello/')

        self.assertUsage('hello', returncode=1)

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': self._options({'prefix': self.prefix}),
            'packages': [{
                'name': 'hello',
                'config_file': config,
                'resolved': False,
                'source': 'tarball',
                '_version': 1,
                'submodules': None,
                'should_deploy': True,
                'builder': self._builder('hello'),
                'url': None,
                'path': {'base': 'cfgdir', 'path': 'broken-bfg.tar.gz'},
                'files': [],
                'srcdir': None,
                'guessed_srcdir': 'hello-bfg',
                'patch': None,
            }],
        })

        self.assertPopen(['mopack', 'deploy'], returncode=1)
        include_prefix = '' if platform_name() == 'windows' else 'include/'
        lib_prefix = '' if platform_name() == 'windows' else 'lib/'
        with pushd(self.prefix):
            self.assertNotExists(include_prefix + 'hello.hpp')
            self.assertNotExists(lib_prefix + 'pkgconfig/hello.pc')


class TestBrokenPatch(CommonTest):
    name = 'broken-patch'
    deploy = True

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-broken-patch.yml')
        self.assertPopen(['mopack', 'resolve', config,
                          '-Pprefix=' + self.prefix], returncode=1)
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')
        self.assertNotExists('mopack/src/hello')
        self.assertNotExists('mopack/build/hello/')

        self.assertUsage('hello', returncode=1)

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': self._options({'prefix': self.prefix}),
            'packages': [{
                'name': 'hello',
                'config_file': config,
                'resolved': False,
                'source': 'tarball',
                '_version': 1,
                'submodules': None,
                'should_deploy': True,
                'builder': self._builder('hello'),
                'url': None,
                'path': {'base': 'cfgdir', 'path': 'broken-bfg.tar.gz'},
                'files': [],
                'srcdir': None,
                'guessed_srcdir': 'hello-bfg',
                'patch': {'base': 'cfgdir', 'path': 'hello-bfg.patch'},
            }],
        })

        self.assertPopen(['mopack', 'deploy'], returncode=1)
        include_prefix = '' if platform_name() == 'windows' else 'include/'
        lib_prefix = '' if platform_name() == 'windows' else 'lib/'
        with pushd(self.prefix):
            self.assertNotExists(include_prefix + 'hello.hpp')
            self.assertNotExists(lib_prefix + 'pkgconfig/hello.pc')
