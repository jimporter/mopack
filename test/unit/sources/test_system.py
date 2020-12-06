from os.path import abspath
from unittest import mock

from . import SourceTest

from mopack.sources import Package
from mopack.sources.apt import AptPackage
from mopack.sources.system import SystemPackage


class TestSystemPackage(SourceTest):
    pkg_type = SystemPackage
    config_file = abspath('/path/to/mopack.yml')
    pkgdir = abspath('/path/to/builddir/mopack')
    deploy_paths = {'prefix': '/usr/local'}

    def test_resolve_path(self):
        pkg = self.make_package('foo')
        pkg.resolve(self.pkgdir, self.deploy_paths)
        with mock.patch('subprocess.run', side_effect=OSError()):
            self.assertEqual(pkg.get_usage(self.pkgdir, None), {
                'type': 'path', 'auto_link': False, 'include_path': [],
                'library_path': [], 'headers': [], 'libraries': ['foo'],
                'compile_flags': [], 'link_flags': [],
            })

    def test_resolve_pkg_config(self):
        pkg = self.make_package('foo')
        pkg.resolve(self.pkgdir, self.deploy_paths)
        with mock.patch('subprocess.run'):
            self.assertEqual(pkg.get_usage(self.pkgdir, None), {
                'type': 'pkg-config', 'path': None, 'pcfiles': ['foo'],
                'extra_args': [],
            })

    def test_auto_link(self):
        pkg = self.make_package('foo', auto_link=True)
        pkg.resolve(self.pkgdir, self.deploy_paths)
        with mock.patch('subprocess.run', side_effect=OSError()):
            self.assertEqual(pkg.get_usage(self.pkgdir, None), {
                'type': 'path', 'auto_link': True, 'include_path': [],
                'library_path': [], 'headers': [], 'libraries': ['foo'],
                'compile_flags': [], 'link_flags': [],
            })

    def test_include_path(self):
        pkg = self.make_package('foo', include_path='/path/to/include')
        pkg.resolve(self.pkgdir, self.deploy_paths)
        with mock.patch('subprocess.run', side_effect=OSError()):
            self.assertEqual(pkg.get_usage(self.pkgdir, None), {
                'type': 'path', 'auto_link': False,
                'include_path': [abspath('/path/to/include')],
                'library_path': [], 'headers': [], 'libraries': ['foo'],
                'compile_flags': [], 'link_flags': [],
            })

    def test_library_path(self):
        pkg = self.make_package('foo', library_path='/path/to/lib')
        pkg.resolve(self.pkgdir, self.deploy_paths)
        with mock.patch('subprocess.run', side_effect=OSError()):
            self.assertEqual(pkg.get_usage(self.pkgdir, None), {
                'type': 'path', 'auto_link': False, 'include_path': [],
                'library_path': [abspath('/path/to/lib')], 'headers': [],
                'libraries': ['foo'], 'compile_flags': [], 'link_flags': [],
            })

    def test_headers(self):
        pkg = self.make_package('foo', headers='foo.hpp')
        pkg.resolve(self.pkgdir, self.deploy_paths)
        with mock.patch('subprocess.run', side_effect=OSError()):
            self.assertEqual(pkg.get_usage(self.pkgdir, None), {
                'type': 'path', 'auto_link': False, 'include_path': [],
                'library_path': [], 'headers': ['foo.hpp'],
                'libraries': ['foo'], 'compile_flags': [], 'link_flags': [],
            })

        pkg = self.make_package('foo', headers=['foo.hpp', 'bar.hpp'])
        pkg.resolve(self.pkgdir, self.deploy_paths)
        with mock.patch('subprocess.run', side_effect=OSError()):
            self.assertEqual(pkg.get_usage(self.pkgdir, None), {
                'type': 'path', 'auto_link': False, 'include_path': [],
                'library_path': [], 'headers': ['foo.hpp', 'bar.hpp'],
                'libraries': ['foo'], 'compile_flags': [], 'link_flags': [],
            })

    def test_libraries(self):
        pkg = self.make_package('foo', libraries='bar')
        pkg.resolve(self.pkgdir, self.deploy_paths)
        with mock.patch('subprocess.run', side_effect=OSError()):
            self.assertEqual(pkg.get_usage(self.pkgdir, None), {
                'type': 'path', 'auto_link': False, 'include_path': [],
                'library_path': [], 'headers': [], 'libraries': ['bar'],
                'compile_flags': [], 'link_flags': [],
            })

        pkg = self.make_package('foo', libraries=['foo', 'bar'])
        pkg.resolve(self.pkgdir, self.deploy_paths)
        with mock.patch('subprocess.run', side_effect=OSError()):
            self.assertEqual(pkg.get_usage(self.pkgdir, None), {
                'type': 'path', 'auto_link': False, 'include_path': [],
                'library_path': [], 'headers': [], 'libraries': ['foo', 'bar'],
                'compile_flags': [], 'link_flags': [],
            })

        pkg = self.make_package('foo', libraries=None)
        pkg.resolve(self.pkgdir, self.deploy_paths)
        with mock.patch('subprocess.run', side_effect=OSError()):
            self.assertEqual(pkg.get_usage(self.pkgdir, None), {
                'type': 'path', 'auto_link': False, 'include_path': [],
                'library_path': [], 'headers': [], 'libraries': [],
                'compile_flags': [], 'link_flags': [],
            })

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        pkg = self.make_package('foo', submodules=submodules_required)
        with mock.patch('subprocess.run', side_effect=OSError()):
            self.assertEqual(pkg.get_usage(self.pkgdir, 'sub'), {
                'type': 'path', 'auto_link': False, 'include_path': [],
                'library_path': [], 'headers': [], 'libraries': ['foo_sub'],
                'compile_flags': [], 'link_flags': [],
            })

        pkg = self.make_package('foo', libraries='bar',
                                submodules=submodules_required)
        with mock.patch('subprocess.run', side_effect=OSError()):
            self.assertEqual(pkg.get_usage(self.pkgdir, 'sub'), {
                'type': 'path', 'auto_link': False, 'include_path': [],
                'library_path': [], 'headers': [],
                'libraries': ['bar', 'foo_sub'], 'compile_flags': [],
                'link_flags': [],
            })

        pkg = self.make_package('foo', submodules=submodules_optional)
        with mock.patch('subprocess.run', side_effect=OSError()):
            self.assertEqual(pkg.get_usage(self.pkgdir, 'sub'), {
                'type': 'path', 'auto_link': False, 'include_path': [],
                'library_path': [], 'headers': [],
                'libraries': ['foo', 'foo_sub'], 'compile_flags': [],
                'link_flags': [],
            })

        pkg = self.make_package('foo', libraries='bar',
                                submodules=submodules_optional)
        with mock.patch('subprocess.run', side_effect=OSError()):
            self.assertEqual(pkg.get_usage(self.pkgdir, 'sub'), {
                'type': 'path', 'auto_link': False, 'include_path': [],
                'library_path': [], 'headers': [],
                'libraries': ['bar', 'foo_sub'], 'compile_flags': [],
                'link_flags': [],
            })

    def test_invalid_submodule(self):
        pkg = self.make_package('foo', submodules={
            'names': ['sub'], 'required': True
        })
        with self.assertRaises(ValueError):
            pkg.get_usage(self.pkgdir, ['invalid'])

    def test_deploy(self):
        pkg = self.make_package('foo')
        # This is a no-op; just make sure it executes ok.
        AptPackage.deploy_all(self.pkgdir, [pkg])

    def test_clean_pre(self):
        oldpkg = self.make_package('foo')
        newpkg = self.make_package(AptPackage, 'foo')

        # System -> Apt
        self.assertEqual(oldpkg.clean_pre(self.pkgdir, newpkg), False)

        # Apt -> nothing
        self.assertEqual(oldpkg.clean_pre(self.pkgdir, None), False)

    def test_clean_post(self):
        oldpkg = self.make_package('foo')
        newpkg = self.make_package(AptPackage, 'foo')

        # System -> Apt
        self.assertEqual(oldpkg.clean_post(self.pkgdir, newpkg), False)

        # Apt -> nothing
        self.assertEqual(oldpkg.clean_post(self.pkgdir, None), False)

    def test_clean_all(self):
        oldpkg = self.make_package('foo')
        newpkg = self.make_package(AptPackage, 'foo')

        # System -> Apt
        self.assertEqual(oldpkg.clean_all(self.pkgdir, newpkg), (False, False))

        # Apt -> nothing
        self.assertEqual(oldpkg.clean_all(self.pkgdir, None), (False, False))

    def test_equality(self):
        pkg = self.make_package('foo')

        self.assertEqual(pkg, self.make_package('foo'))
        self.assertEqual(pkg, self.make_package(
            'foo', config_file='/path/to/mopack2.yml'
        ))

        self.assertNotEqual(pkg, self.make_package('bar'))

    def test_rehydrate(self):
        opts = self.make_options()
        pkg = SystemPackage('foo', _options=opts, config_file=self.config_file)
        data = pkg.dehydrate()
        self.assertEqual(pkg, Package.rehydrate(data, _options=opts))
