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
                          '-Pprefix=' + self.prefix])
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
                common={'deploy_paths': {'prefix': self.prefix}},
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
                    builder=cfg_bfg9000_builder('hello')
                ),
                cfg_directory_pkg(
                    'greeter', config,
                    path={'base': 'cfgdir', 'path': 'greeter-bfg'},
                    builder=cfg_bfg9000_builder('greeter')
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
            self.assertOutput(['mopack', 'list-packages'], dedent("""
                └─ greeter (directory)
                   └─ hello (tarball)
            """).lstrip())
        else:
            self.assertOutput(['mopack', 'list-packages'], dedent("""
                +- greeter (directory)
                   +- hello (tarball)
            """).lstrip())

        self.assertOutput(['mopack', 'list-packages', '--flat'],
                          'hello (tarball)\ngreeter (directory)\n')

    def test_resolve_extra(self):
        config = os.path.join(test_data_dir, 'mopack-nested-extra.yml')
        self.assertPopen(['mopack', 'resolve', config,
                          '-Pprefix=' + self.prefix])
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
                common={'deploy_paths': {'prefix': self.prefix}},
                bfg9000={}
            ),
            'packages': [
                cfg_directory_pkg(
                    'hello', config,
                    path={'base': 'cfgdir', 'path': 'hello-bfg'},
                    builder=cfg_bfg9000_builder(
                        'hello', extra_args=['--extra']
                    )
                ),
                cfg_directory_pkg(
                    'greeter', config,
                    path={'base': 'cfgdir', 'path': 'greeter-bfg'},
                    builder=cfg_bfg9000_builder(
                        'greeter', extra_args=['--extra']
                    )
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
            self.assertOutput(['mopack', 'list-packages'], dedent("""
                ├─ hello (directory)
                └─ greeter (directory)
            """).lstrip())
        else:
            self.assertOutput(['mopack', 'list-packages'], dedent("""
                +- hello (directory)
                +- greeter (directory)
            """).lstrip())

        self.assertOutput(['mopack', 'list-packages', '--flat'],
                          'hello (directory)\ngreeter (directory)\n')
