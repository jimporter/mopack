import json
import os

from . import *


class TestCleanNeeded(IntegrationTest):
    name = 'clean-needed'

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

        self.assertPkgConfigLinkage('greeter')
        self.assertPkgConfigLinkage('hello')

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(bfg9000={}),
            'packages': [
                cfg_directory_pkg(
                    'hello', config,
                    path={'base': 'cfgdir', 'path': 'hello-bfg'},
                    builder=cfg_bfg9000_builder(
                        'hello', extra_args=['--extra']
                    ),
                    linkage=cfg_pkg_config_linkage(pcname='hello')
                ),
                cfg_directory_pkg(
                    'greeter', config,
                    path={'base': 'cfgdir', 'path': 'greeter-bfg'},
                    builder=cfg_bfg9000_builder(
                        'greeter', extra_args=['--extra']
                    ),
                    linkage=cfg_pkg_config_linkage(pcname='greeter')
                ),
            ],
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

        self.assertPkgConfigLinkage('greeter')
        self.assertPkgConfigLinkage('hello')

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
                    builder=cfg_bfg9000_builder('hello'),
                    linkage=cfg_pkg_config_linkage(pcname='hello')
                ),
                cfg_directory_pkg(
                    'greeter', config,
                    path={'base': 'cfgdir', 'path': 'greeter-bfg'},
                    builder=cfg_bfg9000_builder('greeter'),
                    linkage=cfg_pkg_config_linkage(pcname='greeter')
                ),
            ],
        })
