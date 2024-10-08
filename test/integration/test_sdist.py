import json
import os
from unittest import skipIf

from mopack.path import pushd
from mopack.platforms import platform_name

from . import *


class SDistTest(IntegrationTest):
    def check_list_files(self, files, implicit=[]):
        output = json.loads(self.assertPopen(
            mopack_cmd('list-files', '--json')
        ))
        self.assertEqual(output, files)
        output = json.loads(self.assertPopen(
            mopack_cmd('list-files', '-I', '--json')
        ))
        self.assertEqual(output, files + implicit)


class TestDirectory(SDistTest):
    name = 'directory'

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-directory-implicit.yml')
        self.assertPopen(mopack_cmd('resolve', config))
        self.assertNotExists('mopack/src/hello/hello-bfg/build.bfg')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigLinkage('hello')
        implicit_cfg = os.path.join(test_data_dir, 'hello-bfg', 'mopack.yml')
        self.check_list_files([config], [implicit_cfg])

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(bfg9000={}),
            'packages': [
                cfg_directory_pkg(
                    'hello', config,
                    path={'base': 'cfgdir', 'path': 'hello-bfg'},
                    builders=[cfg_bfg9000_builder()],
                    linkage=cfg_pkg_config_linkage(pcname='hello')
                ),
            ],
        })

    def test_resolve_verbose(self):
        config = os.path.join(test_data_dir, 'mopack-directory-implicit.yml')
        output = self.assertPopen(mopack_cmd('--verbose', 'resolve', config))
        cfg_line = r'(?m)^    \$ bfg9000 configure .+\bhello\b.*$'
        self.assertRegex(output, cfg_line)

        self.assertNotExists('mopack/src/hello/hello-bfg/build.bfg')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigLinkage('hello')
        implicit_cfg = os.path.join(test_data_dir, 'hello-bfg', 'mopack.yml')
        self.check_list_files([config], [implicit_cfg])

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(bfg9000={}),
            'packages': [
                cfg_directory_pkg(
                    'hello', config,
                    path={'base': 'cfgdir', 'path': 'hello-bfg'},
                    builders=[cfg_bfg9000_builder()],
                    linkage=cfg_pkg_config_linkage(pcname='hello')
                ),
            ],
        })


class TestTarball(SDistTest):
    name = 'tarball'
    deploy = True

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-tarball.yml')
        self.assertPopen(mopack_cmd(
            'resolve', config, '-dprefix=' + self.prefix
        ))
        self.assertExists('mopack/src/hello/hello-bfg/build.bfg')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigLinkage('hello')
        self.check_list_files([config])

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(
                common={'deploy_dirs': {'prefix': self.prefix}},
                bfg9000={}
            ),
            'packages': [
                cfg_tarball_pkg(
                    'hello', config,
                    path={'base': 'cfgdir', 'path': 'hello-bfg.tar.gz'},
                    guessed_srcdir='hello-bfg',
                    builders=[cfg_bfg9000_builder()],
                    linkage=cfg_pkg_config_linkage(pcname='hello')
                ),
            ],
        })

        self.assertPopen(mopack_cmd('deploy'))
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
        self.assertPopen(mopack_cmd(
            'resolve', config, '-dprefix=' + self.prefix
        ))
        self.assertExists('mopack/src/hello/hello-bfg/build.bfg')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigLinkage('hello')
        self.check_list_files([config])

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(
                common={'deploy_dirs': {'prefix': self.prefix}},
                bfg9000={}
            ),
            'packages': [
                cfg_tarball_pkg(
                    'hello', config,
                    path={'base': 'cfgdir', 'path': 'hello-bfg.tar.gz'},
                    guessed_srcdir='hello-bfg',
                    patch={'base': 'cfgdir', 'path': 'hello-bfg.patch'},
                    builders=[cfg_bfg9000_builder()],
                    linkage=cfg_pkg_config_linkage(pcname='hello')
                ),
            ],
        })

        self.assertPopen(mopack_cmd('deploy'))
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
        self.assertPopen(mopack_cmd(
            'resolve', config, '-dprefix=' + self.prefix
        ))
        self.assertExists('mopack/src/bencodehpp/build.bfg')
        self.assertExists('mopack/build/bencodehpp/')
        self.assertExists('mopack/logs/bencodehpp.log')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigLinkage('bencodehpp')
        implicit_cfg = os.path.join(self.stage, 'mopack', 'src', 'bencodehpp',
                                    'mopack.yml')
        self.check_list_files([config], [implicit_cfg])

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(
                common={'deploy_dirs': {'prefix': self.prefix}},
                bfg9000={}
            ),
            'packages': [
                cfg_git_pkg(
                    'bencodehpp', config,
                    repository='https://github.com/jimporter/bencode.hpp.git',
                    rev=['tag', 'v1.0.1'],
                    builders=[cfg_bfg9000_builder()],
                    linkage=cfg_pkg_config_linkage(pcname='bencodehpp')
                ),
            ],
        })

        self.assertPopen(mopack_cmd('deploy'))
        include_prefix = '' if platform_name() == 'windows' else 'include/'
        lib_prefix = '' if platform_name() == 'windows' else 'lib/'
        with pushd(self.prefix):
            self.assertExists(include_prefix + 'bencode.hpp')
            self.assertExists(lib_prefix + 'pkgconfig/bencodehpp.pc')
