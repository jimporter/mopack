import os
import yaml
from yaml.error import MarkedYAMLError

from . import SourceTest

from mopack.yaml_tools import SafeLineLoader
from mopack.sources import make_package
from mopack.sources.sdist import DirectoryPackage
from mopack.sources.system import SystemPackage


class TestMakePackage(SourceTest):
    pkgdir = os.path.abspath('/path/to/builddir/mopack')

    def pkgconfdir(self, name, pkgconfig='pkgconfig'):
        return os.path.join(self.pkgdir, 'build', name, pkgconfig)

    def test_make(self):
        pkg = make_package('foo', {
            'source': 'directory', 'path': '/path', 'build': 'bfg9000',
            'config_file': '/path/to/mopack.yml'
        })
        self.assertIsInstance(pkg, DirectoryPackage)
        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.submodules, None)
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')
        self.assertEqual(pkg.path, os.path.normpath('/path'))
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
        })
        self.set_options(pkg)
        self.assertIsInstance(pkg, SystemPackage)
        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.submodules, {'names': '*', 'required': True})
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')
        self.assertEqual(pkg.get_usage(self.pkgdir, ['sub']), {
            'type': 'system', 'auto_link': False, 'include_path': [],
            'library_path': [], 'headers': [], 'libraries': ['foo_sub'],
            'compile_flags': [], 'link_flags': [],
        })
        with self.assertRaises(ValueError):
            pkg.get_usage(self.pkgdir, None)

        pkg = make_package('foo', {
            'source': 'system', 'submodules': ['sub'],
            'config_file': '/path/to/mopack.yml'
        })
        self.set_options(pkg)
        self.assertIsInstance(pkg, SystemPackage)
        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.submodules, {'names': ['sub'], 'required': True})
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')
        self.assertEqual(pkg.get_usage(self.pkgdir, ['sub']), {
            'type': 'system', 'auto_link': False, 'include_path': [],
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
        })
        self.set_options(pkg)
        self.assertIsInstance(pkg, SystemPackage)
        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.submodules, {'names': ['sub'], 'required': False})
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')
        self.assertEqual(pkg.get_usage(self.pkgdir, ['sub']), {
            'type': 'system', 'auto_link': False, 'include_path': [],
            'library_path': [], 'headers': [], 'libraries': ['foo', 'foo_sub'],
            'compile_flags': [], 'link_flags': [],
        })
        self.assertEqual(pkg.get_usage(self.pkgdir, None), {
            'type': 'system', 'auto_link': False, 'include_path': [],
            'library_path': [], 'headers': [], 'libraries': ['foo'],
            'compile_flags': [], 'link_flags': [],
        })
        with self.assertRaises(ValueError):
            pkg.get_usage(self.pkgdir, ['bar'])

    def test_boost(self):
        pkg = make_package('boost', {
            'source': 'system', 'config_file': '/path/to/mopack.yml'
        })
        self.assertIsInstance(pkg, SystemPackage)
        self.assertEqual(pkg.name, 'boost')
        self.assertEqual(pkg.submodules, {'names': '*', 'required': False})
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')

    def test_invalid(self):
        self.assertRaises(TypeError, make_package, 'foo',
                          {'source': 'directory'})

    def test_invalid_marked(self):
        data = yaml.load('source: directory', Loader=SafeLineLoader)
        self.assertRaises(MarkedYAMLError, make_package, 'foo', data)

    def test_unknown(self):
        self.assertRaises(ValueError, make_package, 'foo', {'source': 'goofy'})
