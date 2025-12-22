import json
import os

from . import *


class TestCleanNeeded(IntegrationTest):
    name = 'clean-needed'

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-nested-extra.yml')
        self.assertPopen(mopack_cmd('resolve', config))
        self.assertExists('mopack/build/greeter/')
        self.assertExists('mopack/build/greeter/extra.txt')
        self.assertExists('mopack/logs/greeter.log')

        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/build/hello/extra.txt')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        include_greeter = os.path.join(test_data_dir, 'greeter-bfg', 'include')
        include_hello = os.path.join(test_data_dir, 'hello-bfg', 'include')

        self.assertPkgConfigLinkage(
            'greeter', pkg_config_path=[
                os.path.join('build', 'greeter', 'pkgconfig'),
                os.path.join('build', 'hello', 'pkgconfig'),
            ], include_path=[include_greeter, include_hello])
        self.assertPkgConfigLinkage('hello', include_path=[include_hello])

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(bfg9000={}),
            'packages': [
                cfg_directory_pkg(
                    'hello', config,
                    path={'base': 'cfgdir', 'path': 'hello-bfg'},
                    builders=[cfg_bfg9000_builder(extra_args=['--extra'])],
                    linkage=cfg_pkg_config_linkage(pcname='hello')
                ),
                cfg_directory_pkg(
                    'greeter', config,
                    dependencies=['hello'],
                    path={'base': 'cfgdir', 'path': 'greeter-bfg'},
                    builders=[cfg_bfg9000_builder(extra_args=['--extra'])],
                    linkage=cfg_pkg_config_linkage(pcname='greeter')
                ),
            ],
        })

        # Rebuild with a different config.
        config = os.path.join(test_data_dir, 'mopack-nested.yml')
        self.assertPopen(mopack_cmd('resolve', config))
        self.assertExists('mopack/build/greeter/')
        self.assertExists('mopack/logs/greeter.log')
        self.assertExists('mopack/src/hello/hello-bfg/')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')
        self.assertNotExists('mopack/build/greeter/extra.txt')
        self.assertNotExists('mopack/build/hello/extra.txt')

        include_greeter = os.path.join(test_data_dir, 'greeter-bfg', 'include')
        include_hello = os.path.join(self.pkgsrcdir, 'hello', 'hello-bfg',
                                     'include')

        self.assertPkgConfigLinkage(
            'greeter', pkg_config_path=[
                os.path.join('build', 'greeter', 'pkgconfig'),
                os.path.join('build', 'hello', 'pkgconfig'),
            ], include_path=[include_greeter, include_hello])
        self.assertPkgConfigLinkage('hello', include_path=[include_hello])

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(bfg9000={}),
            'packages': [
                cfg_tarball_pkg(
                    'hello',
                    os.path.join(test_data_dir, 'greeter-bfg', 'mopack.yml'),
                    parent='greeter',
                    path={'base': 'cfgdir',
                          'path': os.path.join('..', 'hello-bfg.tar.gz')},
                    guessed_srcdir='hello-bfg',
                    builders=[cfg_bfg9000_builder()],
                    linkage=cfg_pkg_config_linkage(pcname='hello')
                ),
                cfg_directory_pkg(
                    'greeter', config,
                    dependencies=['hello'],
                    path={'base': 'cfgdir', 'path': 'greeter-bfg'},
                    builders=[cfg_bfg9000_builder()],
                    linkage=cfg_pkg_config_linkage(pcname='greeter')
                ),
            ],
        })
