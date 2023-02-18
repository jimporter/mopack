import json
import os
import sys
from textwrap import dedent

from mopack.path import pushd
from mopack.platforms import platform_name

from . import *


class TestNested(IntegrationTest):
    name = 'nested'
    deploy = True

    def setUp(self):
        super().setUp()
        try:
            '┼'.encode(sys.stdout.encoding)
            self.supports_unicode = True
        except UnicodeEncodeError:
            self.supports_unicode = False

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-nested.yml')
        self.assertPopen(['mopack', 'resolve', config,
                          '-dprefix=' + self.prefix])
        self.assertExists('mopack/build/greeter/')
        self.assertExists('mopack/logs/greeter.log')
        self.assertExists('mopack/src/hello/hello-bfg/')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigUsage('greeter')
        self.assertPkgConfigUsage('hello')

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(
                common={'deploy_dirs': {'prefix': self.prefix}},
                bfg9000={}
            ),
            'packages': [
                cfg_tarball_pkg(
                    'hello',
                    os.path.join(test_data_dir, 'greeter-bfg', 'mopack.yml'),
                    parent='greeter',
                    path={'base': 'cfgdir',
                          'path': os.path.join('..', 'hello-bfg.tar.gz')},
                    guessed_srcdir='hello-bfg',
                    builder=cfg_bfg9000_builder('hello'),
                    usage=cfg_pkg_config_usage(pcname='hello')
                ),
                cfg_directory_pkg(
                    'greeter', config,
                    path={'base': 'cfgdir', 'path': 'greeter-bfg'},
                    builder=cfg_bfg9000_builder('greeter'),
                    usage=cfg_pkg_config_usage(pcname='greeter')
                )
            ],
        })

        self.assertPopen(['mopack', 'deploy'])
        include_prefix = '' if platform_name() == 'windows' else 'include/'
        lib_prefix = '' if platform_name() == 'windows' else 'lib/'
        with pushd(self.prefix):
            self.assertExists(include_prefix + 'greeter.hpp')
            self.assertExists(lib_prefix + 'pkgconfig/greeter.pc')
            self.assertExists(include_prefix + 'hello.hpp')
            self.assertExists(lib_prefix + 'pkgconfig/hello.pc')

        if self.supports_unicode:
            self.assertOutput(['mopack', 'list-packages'], dedent("""\
                └─ greeter 1.0 (directory)
                   └─ hello 1.0 (tarball)
            """))
        else:
            self.assertOutput(['mopack', 'list-packages'], dedent("""\
                +- greeter 1.0 (directory)
                   +- hello 1.0 (tarball)
            """))

        self.assertOutput(['mopack', 'list-packages', '--flat'],
                          'hello 1.0 (tarball)\ngreeter 1.0 (directory)\n')

    def test_resolve_extra(self):
        config = os.path.join(test_data_dir, 'mopack-nested-extra.yml')
        self.assertPopen(['mopack', 'resolve', config,
                          '-dprefix=' + self.prefix])
        self.assertExists('mopack/build/greeter/')
        self.assertExists('mopack/logs/greeter.log')
        self.assertNotExists('mopack/src/hello/hello-bfg/')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigUsage('greeter')
        self.assertPkgConfigUsage('hello')

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(
                common={'deploy_dirs': {'prefix': self.prefix}},
                bfg9000={}
            ),
            'packages': [
                cfg_directory_pkg(
                    'hello', config,
                    path={'base': 'cfgdir', 'path': 'hello-bfg'},
                    builder=cfg_bfg9000_builder(
                        'hello', extra_args=['--extra']
                    ),
                    usage=cfg_pkg_config_usage(pcname='hello')
                ),
                cfg_directory_pkg(
                    'greeter', config,
                    path={'base': 'cfgdir', 'path': 'greeter-bfg'},
                    builder=cfg_bfg9000_builder(
                        'greeter', extra_args=['--extra']
                    ),
                    usage=cfg_pkg_config_usage(pcname='greeter')
                )
            ],
        })

        self.assertPopen(['mopack', 'deploy'])
        include_prefix = '' if platform_name() == 'windows' else 'include/'
        lib_prefix = '' if platform_name() == 'windows' else 'lib/'
        with pushd(self.prefix):
            self.assertExists(include_prefix + 'greeter.hpp')
            self.assertExists(lib_prefix + 'pkgconfig/greeter.pc')
            self.assertExists(include_prefix + 'hello.hpp')
            self.assertExists(lib_prefix + 'pkgconfig/hello.pc')

        if self.supports_unicode:
            self.assertOutput(['mopack', 'list-packages'], dedent("""\
                ├─ hello 1.0 (directory)
                └─ greeter 1.0 (directory)
            """))
        else:
            self.assertOutput(['mopack', 'list-packages'], dedent("""\
                +- hello 1.0 (directory)
                +- greeter 1.0 (directory)
            """))

        self.assertOutput(['mopack', 'list-packages', '--flat'],
                          'hello 1.0 (directory)\ngreeter 1.0 (directory)\n')
