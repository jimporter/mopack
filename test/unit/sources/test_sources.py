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
        if name is None:
            return os.path.join(self.pkgdir, pkgconfig)
        else:
            return os.path.join(self.pkgdir, 'build', name, pkgconfig)

    def test_make(self):
        pkg = make_package('foo', {
            'source': 'directory', 'path': '/path', 'build': 'bfg9000',
        }, _options=self.make_options(), config_file='/path/to/mopack.yml')
        self.assertIsInstance(pkg, DirectoryPackage)
        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.submodules, None)
        self.assertEqual(pkg.should_deploy, True)
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')
        self.assertEqual(pkg.path, Path('/path'))
        self.assertEqual(pkg.builder.type, 'bfg9000')

        self.assertEqual(pkg.get_usage(None, self.pkgdir), {
            'name': 'foo', 'type': 'pkg_config',
            'path': [self.pkgconfdir('foo')], 'pcfiles': ['foo'],
            'extra_args': [],
        })
        with self.assertRaises(ValueError):
            pkg.get_usage(['sub'], self.pkgdir)

    def test_make_no_deploy(self):
        pkg = make_package('foo', {
            'source': 'directory', 'path': '/path', 'build': 'bfg9000',
            'deploy': False,
        }, _options=self.make_options(), config_file='/path/to/mopack.yml')
        self.assertIsInstance(pkg, DirectoryPackage)
        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.submodules, None)
        self.assertEqual(pkg.should_deploy, False)
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')
        self.assertEqual(pkg.path, Path('/path'))
        self.assertEqual(pkg.builder.type, 'bfg9000')

        self.assertEqual(pkg.get_usage(None, self.pkgdir), {
            'name': 'foo', 'type': 'pkg_config',
            'path': [self.pkgconfdir('foo')], 'pcfiles': ['foo'],
            'extra_args': [],
        })
        with self.assertRaises(ValueError):
            pkg.get_usage(['sub'], self.pkgdir)

    def test_make_submodules(self):
        pkg = make_package('foo', {
            'source': 'system', 'submodules': '*',
        }, _options=self.make_options(), config_file='/path/to/mopack.yml')
        self.assertIsInstance(pkg, SystemPackage)
        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.submodules, {'names': '*', 'required': True})
        self.assertEqual(pkg.should_deploy, True)
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')
        with mock.patch('subprocess.run', side_effect=OSError()), \
             mock.patch('mopack.usage.path_system.PathUsage._filter_path',
                        lambda *args: []), \
             mock.patch('mopack.usage.path_system.file_outdated',
                        return_value=True), \
             mock.patch('os.makedirs'), \
             mock.patch('builtins.open'):  # noqa
            self.assertEqual(pkg.get_usage(['sub'], self.pkgdir), {
                'name': 'foo', 'type': 'system',
                'path': [self.pkgconfdir(None)], 'pcfiles': ['foo[sub]'],
                'generated': True, 'auto_link': False,
            })
        with self.assertRaises(ValueError):
            pkg.get_usage(None, self.pkgdir)

        pkg = make_package('foo', {
            'source': 'system', 'submodules': ['sub'],
        }, _options=self.make_options(), config_file='/path/to/mopack.yml')
        self.assertIsInstance(pkg, SystemPackage)
        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.submodules, {'names': ['sub'], 'required': True})
        self.assertEqual(pkg.should_deploy, True)
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')
        with mock.patch('subprocess.run', side_effect=OSError()), \
             mock.patch('mopack.usage.path_system.PathUsage._filter_path',
                        lambda *args: []), \
             mock.patch('mopack.usage.path_system.file_outdated',
                        return_value=True), \
             mock.patch('os.makedirs'), \
             mock.patch('builtins.open'):  # noqa
            self.assertEqual(pkg.get_usage(['sub'], self.pkgdir), {
                'name': 'foo', 'type': 'system',
                'path': [self.pkgconfdir(None)], 'pcfiles': ['foo[sub]'],
                'generated': True, 'auto_link': False,
            })
        with self.assertRaises(ValueError):
            pkg.get_usage(['bar'], self.pkgdir)
        with self.assertRaises(ValueError):
            pkg.get_usage(None, self.pkgdir)

        pkg = make_package('foo', {
            'source': 'system',
            'submodules': {'names': ['sub'], 'required': False},
        }, _options=self.make_options(), config_file='/path/to/mopack.yml')
        self.assertIsInstance(pkg, SystemPackage)
        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.submodules, {'names': ['sub'], 'required': False})
        self.assertEqual(pkg.should_deploy, True)
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')
        with mock.patch('subprocess.run', side_effect=OSError()), \
             mock.patch('mopack.usage.path_system.PathUsage._filter_path',
                        lambda *args: []), \
             mock.patch('mopack.usage.path_system.file_outdated',
                        return_value=True), \
             mock.patch('os.makedirs'), \
             mock.patch('builtins.open'):  # noqa
            self.assertEqual(pkg.get_usage(['sub'], self.pkgdir), {
                'name': 'foo', 'type': 'system',
                'path': [self.pkgconfdir(None)], 'pcfiles': ['foo[sub]'],
                'generated': True, 'auto_link': False,
            })
        with mock.patch('subprocess.run', side_effect=OSError()), \
             mock.patch('mopack.usage.path_system.PathUsage._filter_path',
                        lambda *args: []), \
             mock.patch('mopack.usage.path_system.file_outdated',
                        return_value=True), \
             mock.patch('os.makedirs'), \
             mock.patch('builtins.open'):  # noqa
            self.assertEqual(pkg.get_usage(None, self.pkgdir), {
                'name': 'foo', 'type': 'system',
                'path': [self.pkgconfdir(None)], 'pcfiles': ['foo'],
                'generated': True, 'auto_link': False,
            })
        with self.assertRaises(ValueError):
            pkg.get_usage(['bar'], self.pkgdir)

    def test_boost(self):
        pkg = make_package('boost', {
            'source': 'system',
        }, _options=self.make_options(), config_file='/path/to/mopack.yml')
        self.assertIsInstance(pkg, SystemPackage)
        self.assertEqual(pkg.name, 'boost')
        self.assertEqual(pkg.submodules, {'names': '*', 'required': False})
        self.assertEqual(pkg.should_deploy, True)
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')

    def test_unknown_source(self):
        cfg = {'source': 'goofy'}
        self.assertRaises(FieldError, make_package, 'foo', cfg,
                          config_file='/path/to/mopack.yml')
        self.assertRaises(FieldError, try_make_package, 'foo', cfg,
                          config_file='/path/to/mopack.yml')
        data = yaml.load('source: goofy', Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 1, column 9:\n'
                                    r'    source: goofy\n'
                                    r'            \^$'):
            try_make_package('foo', data, _options=self.make_options())

    def test_no_source(self):
        with self.assertRaises(TypeError):
            make_package('boost', None, _options=self.make_options(),
                         config_file='/path/to/mopack.yml')

    def test_invalid_config_file(self):
        with self.assertRaises(FieldError):
            make_package('boost', {
                'source': 'system', 'config_file': '/path/to/mopack.yml',
            }, _options=self.make_options())

    def test_invalid_keys(self):
        # Missing key
        cfg = {'source': 'directory'}
        self.assertRaises(TypeError, make_package, 'foo', cfg,
                          _options=self.make_options(),
                          config_file='/path/to/mopack.yml')
        self.assertRaises(TypeError, try_make_package, 'foo', cfg,
                          _options=self.make_options(),
                          config_file='/path/to/mopack.yml')
        data = yaml.load('source: directory', Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 1, column 1:\n'
                                    r'    source: directory\n'
                                    r'    \^$'):
            try_make_package('foo', data, _options=self.make_options(),
                             config_file='/path/to/mopack.yml')

        # Extra key
        cfg = {'source': 'directory', 'path': '/path', 'unknown': 'blah'}
        self.assertRaises(TypeError, make_package, 'foo', cfg,
                          _options=self.make_options(),
                          config_file='/path/to/mopack.yml')
        self.assertRaises(TypeError, try_make_package, 'foo', cfg,
                          _options=self.make_options(),
                          config_file='/path/to/mopack.yml')
        data = yaml.load(dedent("""\
          source: directory
          path: /path
          unknown: blah
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 3, column 1:\n'
                                    r'    unknown: blah\n'
                                    r'    \^$'):
            try_make_package('foo', data, _options=self.make_options(),
                             config_file='/path/to/mopack.yml')

    def test_invalid_values(self):
        cfg = {'source': 'tarball', 'path': 'file.tar.gz', 'srcdir': '..'}
        self.assertRaises(FieldError, make_package, 'foo', cfg,
                          _options=self.make_options(),
                          config_file='/path/to/mopack.yml')
        self.assertRaises(FieldError, try_make_package, 'foo', cfg,
                          _options=self.make_options(),
                          config_file='/path/to/mopack.yml')
        data = yaml.load(dedent("""\
          source: tarball
          path: file.tar.gz
          srcdir: ..
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 3, column 9:\n'
                                    r'    srcdir: ..\n'
                                    r'            \^$'):
            try_make_package('foo', data, _options=self.make_options(),
                             config_file='/path/to/mopack.yml')

    def test_unknown_builder(self):
        data = yaml.load(dedent("""\
          source: directory
          path: /path
          build: goofy
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 3, column 8:\n'
                                    r'    build: goofy\n'
                                    r'           \^$'):
            try_make_package('foo', data, _options=self.make_options(),
                             config_file='/path/to/mopack.yml')

        data = yaml.load(dedent("""\
          source: directory
          path: /path
          build:
            type: goofy
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 4, column 9:\n'
                                    r'      type: goofy\n'
                                    r'            \^$'):
            try_make_package('foo', data, _options=self.make_options(),
                             config_file='/path/to/mopack.yml')

    def test_invalid_builder_keys(self):
        data = yaml.load(dedent("""\
          source: directory
          path: /path
          build:
            type: bfg9000
            unknown: blah
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 5, column 3:\n'
                                    r'      unknown: blah\n'
                                    r'      \^$'):
            try_make_package('foo', data, _options=self.make_options(),
                             config_file='/path/to/mopack.yml')

    def test_invalid_builder_values(self):
        data = yaml.load(dedent("""\
          source: directory
          path: /path
          build:
            type: bfg9000
            extra_args: 1
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 5, column 15:\n'
                                    r'      extra_args: 1\n'
                                    r'                  \^$'):
            try_make_package('foo', data, _options=self.make_options(),
                             config_file='/path/to/mopack.yml')

    def test_unknown_usage(self):
        data = yaml.load(dedent("""\
          source: apt
          usage: unknown
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 2, column 8:\n'
                                    r'    usage: unknown\n'
                                    r'           \^$'):
            try_make_package('foo', data, _options=self.make_options(),
                             config_file='/path/to/mopack.yml')

        data = yaml.load(dedent("""\
          source: apt
          usage:
            type: unknown
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 3, column 9:\n'
                                    r'      type: unknown\n'
                                    r'            \^$'):
            try_make_package('foo', data, _options=self.make_options(),
                             config_file='/path/to/mopack.yml')

    def test_invalid_usage_keys(self):
        data = yaml.load(dedent("""\
          source: apt
          usage:
            type: pkg_config
            unknown: blah
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 4, column 3:\n'
                                    r'      unknown: blah\n'
                                    r'      \^$'):
            try_make_package('foo', data, _options=self.make_options(),
                             config_file='/path/to/mopack.yml')

    def test_invalid_usage_values(self):
        data = yaml.load(dedent("""\
          source: apt
          usage:
            type: pkg_config
            path: ..
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 4, column 9:\n'
                                    r'      path: ..\n'
                                    r'            \^$'):
            try_make_package('foo', data, _options=self.make_options(),
                             config_file='/path/to/mopack.yml')
