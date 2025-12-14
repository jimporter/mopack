import os
import yaml
from textwrap import dedent
from unittest import mock
from yaml.error import MarkedYAMLError

from . import OriginTest

from mopack.config import Config
from mopack.path import Path
from mopack.origins import make_package, try_make_package
from mopack.origins.sdist import DirectoryPackage
from mopack.origins.system import SystemPackage
from mopack.types import FieldError
from mopack.yaml_tools import SafeLineLoader


class TestMakePackage(OriginTest):
    def pkgconfdir(self, name, pkgconfig='pkgconfig'):
        if name is None:
            return os.path.join(self.pkgdir, pkgconfig)
        else:
            return os.path.join(self.pkgdir, 'build', name, pkgconfig)

    def package_fetch(self, pkg):
        with mock.patch('mopack.config.BaseConfig._accumulate_config'), \
             mock.patch('mopack.yaml_tools.make_parse_error', lambda e, _: e):
            return pkg.fetch(self.metadata, Config([]))

    def test_make(self):
        pkg = make_package('foo', {
            'origin': 'directory', 'path': '/path', 'build': 'bfg9000',
        }, _options=self.make_options(), config_file='/path/to/mopack.yml')
        self.assertIsInstance(pkg, DirectoryPackage)
        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.submodules, None)
        self.assertEqual(pkg.should_deploy, True)
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')
        self.assertEqual(pkg.path, Path('/path'))

        self.package_fetch(pkg)
        self.assertEqual(pkg.builder_types, ['bfg9000'])

        self.assertEqual(pkg.get_linkage(self.metadata, None), {
            'name': 'foo', 'type': 'pkg_config', 'pcnames': ['foo'],
            'pkg_config_path': [self.pkgconfdir('foo')],
        })
        with self.assertRaises(ValueError):
            pkg.get_linkage(self.metadata, ['sub'])

    def test_make_no_deploy(self):
        pkg = make_package('foo', {
            'origin': 'directory', 'path': '/path', 'build': 'bfg9000',
            'deploy': False,
        }, _options=self.make_options(), config_file='/path/to/mopack.yml')
        self.assertIsInstance(pkg, DirectoryPackage)
        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.submodules, None)
        self.assertEqual(pkg.should_deploy, False)
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')
        self.assertEqual(pkg.path, Path('/path'))

        self.package_fetch(pkg)
        self.assertEqual(pkg.builder_types, ['bfg9000'])

        self.assertEqual(pkg.get_linkage(self.metadata, None), {
            'name': 'foo', 'type': 'pkg_config', 'pcnames': ['foo'],
            'pkg_config_path': [self.pkgconfdir('foo')],
        })
        with self.assertRaises(ValueError):
            pkg.get_linkage(self.metadata, ['sub'])

    def test_make_submodules(self):
        pkg = make_package('foo', {
            'origin': 'system', 'submodules': '*',
        }, _options=self.make_options(), config_file='/path/to/mopack.yml')
        self.assertIsInstance(pkg, SystemPackage)
        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.submodules, {'names': '*', 'required': True})
        self.assertEqual(pkg.should_deploy, True)
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')
        with mock.patch('subprocess.run', side_effect=OSError()), \
             mock.patch('mopack.linkages.path_system.PathLinkage._filter_path',
                        lambda *args: []), \
             mock.patch('mopack.linkages.path_system.file_outdated',
                        return_value=True), \
             mock.patch('os.makedirs'), \
             mock.patch('builtins.open'):
            self.assertEqual(pkg.get_linkage(self.metadata, ['sub']), {
                'name': 'foo[sub]', 'type': 'system', 'generated': True,
                'auto_link': False, 'pcnames': ['foo[sub]'],
                'pkg_config_path': [self.pkgconfdir(None)],
            })
        with self.assertRaises(ValueError):
            pkg.get_linkage(self.metadata, None)

        pkg = make_package('foo', {
            'origin': 'system', 'submodules': ['sub'],
        }, _options=self.make_options(), config_file='/path/to/mopack.yml')
        self.assertIsInstance(pkg, SystemPackage)
        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.submodules, {'names': ['sub'], 'required': True})
        self.assertEqual(pkg.should_deploy, True)
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')
        with mock.patch('subprocess.run', side_effect=OSError()), \
             mock.patch('mopack.linkages.path_system.PathLinkage._filter_path',
                        lambda *args: []), \
             mock.patch('mopack.linkages.path_system.file_outdated',
                        return_value=True), \
             mock.patch('os.makedirs'), \
             mock.patch('builtins.open'):
            self.assertEqual(pkg.get_linkage(self.metadata, ['sub']), {
                'name': 'foo[sub]', 'type': 'system', 'generated': True,
                'auto_link': False, 'pcnames': ['foo[sub]'],
                'pkg_config_path': [self.pkgconfdir(None)],
            })
        with self.assertRaises(ValueError):
            pkg.get_linkage(self.metadata, ['bar'])
        with self.assertRaises(ValueError):
            pkg.get_linkage(self.metadata, None)

        pkg = make_package('foo', {
            'origin': 'system',
            'submodules': {'names': ['sub'], 'required': False},
        }, _options=self.make_options(), config_file='/path/to/mopack.yml')
        self.assertIsInstance(pkg, SystemPackage)
        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.submodules, {'names': ['sub'], 'required': False})
        self.assertEqual(pkg.should_deploy, True)
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')
        with mock.patch('subprocess.run', side_effect=OSError()), \
             mock.patch('mopack.linkages.path_system.PathLinkage._filter_path',
                        lambda *args: []), \
             mock.patch('mopack.linkages.path_system.file_outdated',
                        return_value=True), \
             mock.patch('os.makedirs'), \
             mock.patch('builtins.open'):
            self.assertEqual(pkg.get_linkage(self.metadata, ['sub']), {
                'name': 'foo[sub]', 'type': 'system', 'generated': True,
                'auto_link': False, 'pcnames': ['foo[sub]'],
                'pkg_config_path': [self.pkgconfdir(None)],
            })
        with mock.patch('subprocess.run', side_effect=OSError()), \
             mock.patch('mopack.linkages.path_system.PathLinkage._filter_path',
                        lambda *args: []), \
             mock.patch('mopack.linkages.path_system.file_outdated',
                        return_value=True), \
             mock.patch('os.makedirs'), \
             mock.patch('builtins.open'):
            self.assertEqual(pkg.get_linkage(self.metadata, None), {
                'name': 'foo', 'type': 'system', 'generated': True,
                'auto_link': False, 'pcnames': ['foo'],
                'pkg_config_path': [self.pkgconfdir(None)],
            })
        with self.assertRaises(ValueError):
            pkg.get_linkage(self.metadata, ['bar'])

    def test_boost(self):
        pkg = make_package('boost', {
            'origin': 'system',
        }, _options=self.make_options(), config_file='/path/to/mopack.yml')
        self.assertIsInstance(pkg, SystemPackage)
        self.assertEqual(pkg.name, 'boost')
        self.assertEqual(pkg.submodules, {'names': '*', 'required': False})
        self.assertEqual(pkg.should_deploy, True)
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')

    def test_unknown_origin(self):
        cfg = {'origin': 'goofy'}
        self.assertRaises(FieldError, make_package, 'foo', cfg,
                          config_file='/path/to/mopack.yml')
        self.assertRaises(FieldError, try_make_package, 'foo', cfg,
                          config_file='/path/to/mopack.yml')
        data = yaml.load('origin: goofy', Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 1, column 9:\n'
                                    r'    origin: goofy\n'
                                    r'            \^$'):
            try_make_package('foo', data, _options=self.make_options())

    def test_no_origin(self):
        with self.assertRaises(TypeError):
            make_package('boost', None, _options=self.make_options(),
                         config_file='/path/to/mopack.yml')

    def test_invalid_config_file(self):
        with self.assertRaises(FieldError):
            make_package('boost', {
                'origin': 'system', 'config_file': '/path/to/mopack.yml',
            }, _options=self.make_options())

    def test_invalid_keys(self):
        # Missing key
        cfg = {'origin': 'directory'}
        self.assertRaises(TypeError, make_package, 'foo', cfg,
                          _options=self.make_options(),
                          config_file='/path/to/mopack.yml')
        self.assertRaises(TypeError, try_make_package, 'foo', cfg,
                          _options=self.make_options(),
                          config_file='/path/to/mopack.yml')
        data = yaml.load('origin: directory', Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 1, column 1:\n'
                                    r'    origin: directory\n'
                                    r'    \^$'):
            try_make_package('foo', data, _options=self.make_options(),
                             config_file='/path/to/mopack.yml')

        # Extra key
        cfg = {'origin': 'directory', 'path': '/path', 'unknown': 'blah'}
        self.assertRaises(TypeError, make_package, 'foo', cfg,
                          _options=self.make_options(),
                          config_file='/path/to/mopack.yml')
        self.assertRaises(TypeError, try_make_package, 'foo', cfg,
                          _options=self.make_options(),
                          config_file='/path/to/mopack.yml')
        data = yaml.load(dedent("""\
          origin: directory
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
        cfg = {'origin': 'tarball', 'path': 'file.tar.gz', 'srcdir': '..'}
        self.assertRaises(FieldError, make_package, 'foo', cfg,
                          _options=self.make_options(),
                          config_file='/path/to/mopack.yml')
        self.assertRaises(FieldError, try_make_package, 'foo', cfg,
                          _options=self.make_options(),
                          config_file='/path/to/mopack.yml')
        data = yaml.load(dedent("""\
          origin: tarball
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
          origin: directory
          path: /path
          build: goofy
        """), Loader=SafeLineLoader)
        pkg = try_make_package('foo', data, _options=self.make_options(),
                               config_file='/path/to/mopack.yml')
        # We can't get the file/line info for builders that are simple strings.
        # Instead, we'll just get a `FieldError`.
        with self.assertRaises(FieldError):
            self.package_fetch(pkg)

        data = yaml.load(dedent("""\
          origin: directory
          path: /path
          build:
            type: goofy
        """), Loader=SafeLineLoader)
        pkg = try_make_package('foo', data, _options=self.make_options(),
                               config_file='/path/to/mopack.yml')
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 4, column 9:\n'
                                    r'      type: goofy\n'
                                    r'            \^$'):
            self.package_fetch(pkg)

    def test_invalid_builder_keys(self):
        data = yaml.load(dedent("""\
          origin: directory
          path: /path
          build:
            type: bfg9000
            unknown: blah
        """), Loader=SafeLineLoader)
        pkg = try_make_package('foo', data, _options=self.make_options(),
                               config_file='/path/to/mopack.yml')
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 5, column 3:\n'
                                    r'      unknown: blah\n'
                                    r'      \^$'):
            self.package_fetch(pkg)

    def test_invalid_builder_values(self):
        data = yaml.load(dedent("""\
          origin: directory
          path: /path
          build:
            type: bfg9000
            extra_args: 1
        """), Loader=SafeLineLoader)
        pkg = try_make_package('foo', data, _options=self.make_options(),
                               config_file='/path/to/mopack.yml')
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 5, column 15:\n'
                                    r'      extra_args: 1\n'
                                    r'                  \^$'):
            self.package_fetch(pkg)

    def test_unknown_linkage(self):
        data = yaml.load(dedent("""\
          origin: apt
          linkage: unknown
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 2, column 10:\n'
                                    r'    linkage: unknown\n'
                                    r'             \^$'):
            try_make_package('foo', data, _options=self.make_options(),
                             config_file='/path/to/mopack.yml')

        data = yaml.load(dedent("""\
          origin: apt
          linkage:
            type: unknown
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 3, column 9:\n'
                                    r'      type: unknown\n'
                                    r'            \^$'):
            try_make_package('foo', data, _options=self.make_options(),
                             config_file='/path/to/mopack.yml')

    def test_invalid_linkage_keys(self):
        data = yaml.load(dedent("""\
          origin: apt
          linkage:
            type: pkg_config
            unknown: blah
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 4, column 3:\n'
                                    r'      unknown: blah\n'
                                    r'      \^$'):
            try_make_package('foo', data, _options=self.make_options(),
                             config_file='/path/to/mopack.yml')

    def test_invalid_linkage_values(self):
        data = yaml.load(dedent("""\
          origin: apt
          linkage:
            type: pkg_config
            pkg_config_path: ..
        """), Loader=SafeLineLoader)
        with self.assertRaisesRegex(MarkedYAMLError,
                                    r'line 4, column 20:\n'
                                    r'      pkg_config_path: ..\n'
                                    r'                       \^$'):
            try_make_package('foo', data, _options=self.make_options(),
                             config_file='/path/to/mopack.yml')
