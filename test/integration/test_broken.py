import json
import os

from mopack.path import pushd
from mopack.platforms import platform_name

from . import *


class TestBroken(IntegrationTest):
    name = 'broken'
    deploy = True

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-broken.yml')
        self.assertPopen(mopack_cmd(
            'resolve', config, '-dprefix=' + self.prefix
        ), returncode=1)
        self.assertExists('mopack/src/hello/hello-bfg/build.bfg')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')
        self.assertNotExists('mopack/build/hello/')

        self.assertLinkage('hello', returncode=1)

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(
                common={'deploy_dirs': {'prefix': self.prefix}},
                bfg9000={}
            ),
            'packages': [
                cfg_tarball_pkg(
                    'hello', config,
                    resolved=False,
                    path={'base': 'cfgdir', 'path': 'broken-bfg.tar.gz'},
                    guessed_srcdir='hello-bfg',
                    builders=[cfg_bfg9000_builder()],
                    linkage=cfg_pkg_config_linkage(pcname='hello')
                ),
            ],
        })

        self.assertPopen(mopack_cmd('deploy'), returncode=1)
        include_prefix = '' if platform_name() == 'windows' else 'include/'
        lib_prefix = '' if platform_name() == 'windows' else 'lib/'
        with pushd(self.prefix):
            self.assertNotExists(include_prefix + 'hello.hpp')
            self.assertNotExists(lib_prefix + 'pkgconfig/hello.pc')


class TestBrokenPatch(IntegrationTest):
    name = 'broken-patch'
    deploy = True

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-broken-patch.yml')
        self.assertPopen(mopack_cmd(
            'resolve', config, '-dprefix=' + self.prefix
        ), returncode=1)
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')
        self.assertNotExists('mopack/src/hello')
        self.assertNotExists('mopack/build/hello/')

        self.assertLinkage('hello', returncode=1)

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(
                common={'deploy_dirs': {'prefix': self.prefix}},
                bfg9000={}
            ),
            'packages': [
                cfg_tarball_pkg(
                    'hello', config,
                    resolved=False,
                    path={'base': 'cfgdir', 'path': 'broken-bfg.tar.gz'},
                    guessed_srcdir='hello-bfg',
                    patch={'base': 'cfgdir', 'path': 'hello-bfg.patch'},
                    builders=[cfg_bfg9000_builder()],
                    linkage=cfg_pkg_config_linkage(pcname='hello')
                ),
            ],
        })

        self.assertPopen(mopack_cmd('deploy'), returncode=1)
        include_prefix = '' if platform_name() == 'windows' else 'include/'
        lib_prefix = '' if platform_name() == 'windows' else 'lib/'
        with pushd(self.prefix):
            self.assertNotExists(include_prefix + 'hello.hpp')
            self.assertNotExists(lib_prefix + 'pkgconfig/hello.pc')
