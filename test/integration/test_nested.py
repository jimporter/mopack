import json
import os

from mopack.path import pushd

from . import *


class TestNested(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('nested')
        self.prefix = stage_dir('nested-install', chdir=False)
        self.pkgbuilddir = os.path.join(self.stage, 'mopack', 'build')

    def _builder(self, name):
        return {
            'type': 'bfg9000',
            'name': name,
            'extra_args': [],
            'usage': {
                'type': 'pkgconfig',
                'path': 'pkgconfig',
            },
        }

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-nested.yml')
        self.assertPopen(['mopack', 'resolve', config,
                          '-Pprefix=' + self.prefix])
        self.assertExists('mopack/build/greeter/')
        self.assertExists('mopack/greeter.log')
        self.assertExists('mopack/src/hello/bfg_project/')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/hello.log')
        self.assertExists('mopack/mopack.json')

        output = json.loads(self.assertPopen(['mopack', 'info', 'greeter']))
        self.assertEqual(output, {
            'config': {
                'name': 'greeter',
                'config_file': config,
                'source': 'directory',
                'builder': self._builder('greeter'),
                'path': os.path.join(test_data_dir, 'nested'),
            },
            'usage': {
                'type': 'pkgconfig',
                'path': os.path.join(self.pkgbuilddir, 'greeter', 'pkgconfig'),
            }
        })

        output = json.loads(self.assertPopen(['mopack', 'info', 'hello']))
        self.assertEqual(output, {
            'config': {
                'name': 'hello',
                'config_file': os.path.join(test_data_dir, 'nested',
                                            'mopack.yml'),
                'source': 'tarball',
                'builder': self._builder('hello'),
                'url': None,
                'path': os.path.join(test_data_dir, 'bfg_project.tar.gz'),
                'files': None,
                'srcdir': None,
                'guessed_srcdir': 'bfg_project',
            },
            'usage': {
                'type': 'pkgconfig',
                'path': os.path.join(self.pkgbuilddir, 'hello', 'pkgconfig'),
            }
        })

        self.assertPopen(['mopack', 'deploy'])
        with pushd(self.prefix):
            self.assertExists('include/greeter.hpp')
            self.assertExists('lib/pkgconfig/greeter.pc')
            self.assertExists('include/hello.hpp')
            self.assertExists('lib/pkgconfig/hello.pc')
