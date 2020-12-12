import os
import yaml
from textwrap import dedent
from unittest import mock
from yaml.error import MarkedYAMLError

from . import SourceTest

from mopack.path import Path
from mopack.sources import make_package, try_make_package
from mopack.sources.sdist import DirectoryPackage
from mopack.sources.system import SystemPackage
from mopack.types import FieldError
from mopack.yaml_tools import SafeLineLoader


class TestMakePackage(SourceTest):
    pkgdir = os.path.abspath('/path/to/builddir/mopack')

    def pkgconfdir(self, name, pkgconfig='pkgconfig'):
        return os.path.join(self.pkgdir, 'build', name, pkgconfig)

    def test_make(self):
        pkg = make_package('foo', {
            'source': 'directory', 'path': '/path', 'build': 'bfg9000',
            'config_file': '/path/to/mopack.yml'
        }, _options=self.make_options())
        self.assertIsInstance(pkg, DirectoryPackage)
        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.submodules, None)
        self.assertEqual(pkg.should_deploy, True)
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')
        self.assertEqual(pkg.path, Path('absolute', '/path'))
        self.assertEqual(pkg.builder.type, 'bfg9000')

        self.assertEqual(pkg.get_usage(self.pkgdir, None), {
            'type': 'pkg-config', 'path': self.pkgconfdir('foo'),
            'pcfiles': ['foo'], 'extra_args': [],
        })
        with self.assertRaises(ValueError):
            pkg.get_usage(self.pkgdir, ['sub'])

    def test_make_no_deploy(self):
        pkg = make_package('foo', {
            'source': 'directory', 'path': '/path', 'build': 'bfg9000',
            'deploy': False, 'config_file': '/path/to/mopack.yml'
        }, _options=self.make_options())
        self.assertIsInstance(pkg, DirectoryPackage)
        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.submodules, None)
        self.assertEqual(pkg.should_deploy, False)
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')
        self.assertEqual(pkg.path, Path('absolute', '/path'))
        self.assertEqual(pkg.builder.type, 'bfg9000')

        self.assertEqual(pkg.get_usage(self.pkgdir, None), {
            'type': 'pkg-config', 'path': self.pkgconfdir('foo'),
            'pcfiles': ['foo'], 'extra_args': [],
        })
        with self.assertRaises(ValueError):
            pkg.get_usage(self.pkgdir, ['sub'])

    def test_make_submodules(self):
        pkg = make_package('foo', {
            'source': 'system', 'submodules': '*',
            'config_file': '/path/to/mopack.yml'
        }, _options=self.make_options())
        self.assertIsInstance(pkg, SystemPackage)
        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.submodules, {'names': '*', 'required': True})
        self.assertEqual(pkg.should_deploy, True)
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')
        with mock.patch('subprocess.run', side_effect=OSError()):
            self.assertEqual(pkg.get_usage(self.pkgdir, ['sub']), {
                'type': 'path', 'auto_link': False, 'include_path': [],
                'library_path': [], 'headers': [], 'libraries': ['foo_sub'],
                'compile_flags': [], 'link_flags': [],
            })
        with self.assertRaises(ValueError):
            pkg.get_usage(self.pkgdir, None)

        pkg = make_package('foo', {
            'source': 'system', 'submodules': ['sub'],
            'config_file': '/path/to/mopack.yml'
        }, _options=self.make_options())
        self.assertIsInstance(pkg, SystemPackage)
        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.submodules, {'names': ['sub'], 'required': True})
        self.assertEqual(pkg.should_deploy, True)
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')
        with mock.patch('subprocess.run', side_effect=OSError()):
            self.assertEqual(pkg.get_usage(self.pkgdir, ['sub']), {
                'type': 'path', 'auto_link': False, 'include_path': [],
                'library_path': [], 'headers': [], 'libraries': ['foo_sub'],
                'compile_flags': [], 'link_flags': [],
            })
        with self.assertRaises(ValueError):
            pkg.get_usage(self.pkgdir, ['bar'])
        with self.assertRaises(ValueError):
            pkg.get_usage(self.pkgdir, None)

        pkg = make_package('foo', {
            'source': 'system',
            'submodules': {'names': ['sub'], 'required': False},
            'config_file': '/path/to/mopack.yml'
        }, _options=self.make_options())
        self.assertIsInstance(pkg, SystemPackage)
        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.submodules, {'names': ['sub'], 'required': False})
        self.assertEqual(pkg.should_deploy, True)
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')
        with mock.patch('subprocess.run', side_effect=OSError()):
            self.assertEqual(pkg.get_usage(self.pkgdir, ['sub']), {
                'type': 'path', 'auto_link': False, 'include_path': [],
                'library_path': [], 'headers': [],
                'libraries': ['foo', 'foo_sub'], 'compile_flags': [],
                'link_flags': [],
            })
        with mock.patch('subprocess.run', side_effect=OSError()):
            self.assertEqual(pkg.get_usage(self.pkgdir, None), {
                'type': 'path', 'auto_link': False, 'include_path': [],
                'library_path': [], 'headers': [], 'libraries': ['foo'],
                'compile_flags': [], 'link_flags': [],
            })
        with self.assertRaises(ValueError):
            pkg.get_usage(self.pkgdir, ['bar'])

    def test_boost(self):
        pkg = make_package('boost', {
            'source': 'system', 'config_file': '/path/to/mopack.yml'
        }, _options=self.make_options())
        self.assertIsInstance(pkg, SystemPackage)
        self.assertEqual(pkg.name, 'boost')
        self.assertEqual(pkg.submodules, {'names': '*', 'required': False})
        self.assertEqual(pkg.should_deploy, True)
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')

    def test_unknown_source(self):
        cfg = {'source': 'goofy', 'config_file': '/path/to/mopack.yml'}
        self.assertRaises(FieldError, make_package, 'foo', cfg)
        self.assertRaises(FieldError, try_make_package, 'foo', cfg)
        data = yaml.load('source: goofy', Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 1, column 9:\n'
                                    r'    source: goofy\n'
                                    r'            \^$'):
            try_make_package('foo', data, _options=self.make_options())

    def test_invalid_keys(self):
        # Missing key
        cfg = {'source': 'directory', 'config_file': '/path/to/mopack.yml'}
        self.assertRaises(TypeError, make_package, 'foo', cfg,
                          _options=self.make_options())
        self.assertRaises(TypeError, try_make_package, 'foo', cfg,
                          _options=self.make_options())
        data = yaml.load(dedent("""
          source: directory
          config_file: /path/to/mopack.yml
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 2, column 1:\n'
                                    r'    source: directory\n'
                                    r'    \^$'):
            try_make_package('foo', data, _options=self.make_options())

        # Extra key
        cfg = {'source': 'directory', 'path': '/path', 'unknown': 'blah',
               'config_file': '/path/to/mopack.yml'}
        self.assertRaises(TypeError, make_package, 'foo', cfg,
                          _options=self.make_options())
        self.assertRaises(TypeError, try_make_package, 'foo', cfg,
                          _options=self.make_options())
        data = yaml.load(dedent("""
          source: directory
          path: /path
          unknown: blah
          config_file: /path/to/mopack.yml
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 4, column 10:\n'
                                    r'    unknown: blah\n'
                                    r'             \^$'):
            try_make_package('foo', data, _options=self.make_options())

    def test_invalid_values(self):
        cfg = {'source': 'tarball', 'path': 'file.tar.gz', 'srcdir': '..',
               'config_file': '/path/to/mopack.yml'}
        self.assertRaises(FieldError, make_package, 'foo', cfg,
                          _options=self.make_options())
        self.assertRaises(FieldError, try_make_package, 'foo', cfg,
                          _options=self.make_options())
        data = yaml.load(dedent("""
          source: tarball
          path: file.tar.gz
          srcdir: ..
          config_file: /path/to/mopack.yml
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 4, column 9:\n'
                                    r'    srcdir: ..\n'
                                    r'            \^$'):
            try_make_package('foo', data, _options=self.make_options())

    def test_unknown_builder(self):
        data = yaml.load(dedent("""
          source: directory
          path: /path
          build: goofy
          config_file: /path/to/mopack.yml
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 4, column 8:\n'
                                    r'    build: goofy\n'
                                    r'           \^$'):
            try_make_package('foo', data, _options=self.make_options())

        data = yaml.load(dedent("""
          source: directory
          path: /path
          build:
            type: goofy
          config_file: /path/to/mopack.yml
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 5, column 9:\n'
                                    r'      type: goofy\n'
                                    r'            \^$'):
            try_make_package('foo', data, _options=self.make_options())

    def test_invalid_builder_keys(self):
        data = yaml.load(dedent("""
          source: directory
          path: /path
          build:
            type: bfg9000
            unknown: blah
          config_file: /path/to/mopack.yml
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 6, column 12:\n'
                                    r'      unknown: blah\n'
                                    r'               \^$'):
            try_make_package('foo', data, _options=self.make_options())

    def test_invalid_builder_values(self):
        data = yaml.load(dedent("""
          source: directory
          path: /path
          build:
            type: bfg9000
            extra_args: 1
          config_file: /path/to/mopack.yml
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 6, column 15:\n'
                                    r'      extra_args: 1\n'
                                    r'                  \^$'):
            try_make_package('foo', data, _options=self.make_options())

    def test_unknown_usage(self):
        data = yaml.load(dedent("""
          source: apt
          usage: unknown
          config_file: /path/to/mopack.yml
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 3, column 8:\n'
                                    r'    usage: unknown\n'
                                    r'           \^$'):
            try_make_package('foo', data, _options=self.make_options())

        data = yaml.load(dedent("""
          source: apt
          usage:
            type: unknown
          config_file: /path/to/mopack.yml
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 4, column 9:\n'
                                    r'      type: unknown\n'
                                    r'            \^$'):
            try_make_package('foo', data, _options=self.make_options())

    def test_invalid_usage_keys(self):
        data = yaml.load(dedent("""
          source: apt
          usage:
            type: pkg-config
            unknown: blah
          config_file: /path/to/mopack.yml
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 5, column 12:\n'
                                    r'      unknown: blah\n'
                                    r'               \^$'):
            try_make_package('foo', data, _options=self.make_options())

    def test_invalid_usage_values(self):
        data = yaml.load(dedent("""
          source: apt
          usage:
            type: pkg-config
            path: ..
          config_file: /path/to/mopack.yml
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 5, column 9:\n'
                                    r'      path: ..\n'
                                    r'            \^$'):
            try_make_package('foo', data, _options=self.make_options())
