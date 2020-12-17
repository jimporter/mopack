import json
import os
from unittest import skipIf

from mopack.path import pushd
from mopack.platforms import platform_name

from . import *


class SDistTest(IntegrationTest):
    def check_list_files(self, files, implicit=[]):
        output = json.loads(self.assertPopen(['mopack', 'list-files',
                                              '--json']))
        self.assertEqual(output, files)
        output = json.loads(self.assertPopen(['mopack', 'list-files', '-I',
                                              '--json']))
        self.assertEqual(output, files + implicit)

    def _options(self, deploy_paths={}):
        return {
            'common': {
                'target_platform': platform_name(),
                'env': AlwaysEqual(),
                'deploy_paths': deploy_paths,
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


class TestDirectory(SDistTest):
    name = 'directory'

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-directory-implicit.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertNotExists('mopack/src/hello/hello-bfg/build.bfg')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigUsage('hello')
        implicit_cfg = os.path.join(test_data_dir, 'hello-bfg', 'mopack.yml')
        self.check_list_files([config], [implicit_cfg])

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': self._options(),
            'packages': [{
                'name': 'hello',
                'config_file': config,
                'resolved': True,
                'source': 'directory',
                'submodules': None,
                'should_deploy': True,
                'builder': self._builder('hello'),
                'path': {'base': 'cfgdir', 'path': 'hello-bfg'},
            }],
        })


class TestTarball(SDistTest):
    name = 'tarball'
    deploy = True

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-tarball.yml')
        self.assertPopen(['mopack', 'resolve', config,
                          '-Pprefix=' + self.prefix])
        self.assertExists('mopack/src/hello/hello-bfg/build.bfg')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigUsage('hello')
        self.check_list_files([config])

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': self._options({'prefix': self.prefix}),
            'packages': [{
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
            }],
        })

        self.assertPopen(['mopack', 'deploy'])
        include_prefix = '' if platform_name() == 'windows' else 'include/'
        lib_prefix = '' if platform_name() == 'windows' else 'lib/'
        with pushd(self.prefix):
            self.assertExists(include_prefix + 'hello.hpp')
            self.assertExists(lib_prefix + 'pkgconfig/hello.pc')


class TestTarballPatch(SDistTest):
    name = 'tarball-patch'
    deploy = True

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-tarball-patch.yml')
        self.assertPopen(['mopack', 'resolve', config,
                          '-Pprefix=' + self.prefix])
        self.assertExists('mopack/src/hello/hello-bfg/build.bfg')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigUsage('hello')
        self.check_list_files([config])

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': self._options({'prefix': self.prefix}),
            'packages': [{
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
                'patch': {'base': 'cfgdir', 'path': 'hello-bfg.patch'},
            }],
        })

        self.assertPopen(['mopack', 'deploy'])
        include_prefix = '' if platform_name() == 'windows' else 'include/'
        lib_prefix = '' if platform_name() == 'windows' else 'lib/'
        with pushd(self.prefix):
            self.assertExists(include_prefix + 'hello.hpp')
            self.assertExists(lib_prefix + 'pkgconfig/hello.pc')


@skipIf('boost' not in test_features, 'skipping test requiring boost')
class TestGit(SDistTest):
    name = 'git'
    deploy = True

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-git.yml')
        self.assertPopen(['mopack', 'resolve', config,
                          '-Pprefix=' + self.prefix])
        self.assertExists('mopack/src/bencodehpp/build.bfg')
        self.assertExists('mopack/build/bencodehpp/')
        self.assertExists('mopack/logs/bencodehpp.log')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigUsage('bencodehpp')
        self.check_list_files([config])

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': self._options({'prefix': self.prefix}),
            'packages': [{
                'name': 'bencodehpp',
                'config_file': config,
                'resolved': True,
                'source': 'git',
                'submodules': None,
                'should_deploy': True,
                'builder': self._builder('bencodehpp'),
                'repository': 'https://github.com/jimporter/bencode.hpp.git',
                'rev': ['tag', 'v0.2.1'],
                'srcdir': '.',
            }],
        })

        self.assertPopen(['mopack', 'deploy'])
        include_prefix = '' if platform_name() == 'windows' else 'include/'
        lib_prefix = '' if platform_name() == 'windows' else 'lib/'
        with pushd(self.prefix):
            self.assertExists(include_prefix + 'bencode.hpp')
            self.assertExists(lib_prefix + 'pkgconfig/bencodehpp.pc')
