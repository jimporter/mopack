import os
import shutil
from os.path import abspath
from unittest import mock

from . import SourceTest
from ... import call_pkg_config, test_stage_dir

from mopack.path import Path
from mopack.sources import Package
from mopack.sources.apt import AptPackage
from mopack.sources.system import SystemPackage
from mopack.types import dependency_string, FieldKeyError


class TestSystemPackage(SourceTest):
    pkg_type = SystemPackage
    pkgdir = os.path.join(test_stage_dir, 'sources')
    pkgconfdir = os.path.join(pkgdir, 'pkgconfig')

    def setUp(self):
        super().setUp()
        self.clear_pkgdir()

    def clear_pkgdir(self):
        if os.path.exists(self.pkgdir):
            shutil.rmtree(self.pkgdir)

    def check_get_usage(self, pkg, submodules, expected=None, *,
                        find_pkg_config=False):
        def mock_isfile(p, variables={}):
            p = os.path.normcase(p.string(**variables))
            return p.startswith(os.path.normcase(abspath('/mock')) + os.sep)

        if expected is None:
            depname = dependency_string(pkg.name, submodules)
            expected = {'name': depname, 'type': 'system', 'generated': True,
                        'auto_link': False, 'path': [self.pkgconfdir],
                        'pcfiles': [depname]}

        self.clear_pkgdir()
        side_effect = None if find_pkg_config else OSError()
        with mock.patch('subprocess.run', side_effect=side_effect), \
             mock.patch('mopack.usage.path_system.file_outdated',
                        return_value=True), \
             mock.patch('mopack.usage.path_system._system_include_path',
                        return_value=[Path('/mock/include')]), \
             mock.patch('mopack.usage.path_system._system_lib_path',
                        return_value=[Path('/mock/lib')]), \
             mock.patch('mopack.usage.path_system._system_lib_names',
                        return_value=['lib{}.so']), \
             mock.patch('mopack.usage.path_system.isfile',
                        mock_isfile):
            self.assertEqual(pkg.get_usage(self.metadata, submodules),
                             expected)

    def check_pkg_config(self, name, submodules, expected={}):
        pcname = dependency_string(name, submodules)
        self.assertCountEqual(
            call_pkg_config(pcname, ['--cflags'], path=self.pkgconfdir),
            expected.get('cflags', [])
        )
        self.assertCountEqual(
            call_pkg_config(pcname, ['--libs'], path=self.pkgconfdir),
            expected.get('libs', ['-L' + abspath('/mock/lib'), '-l' + name])
        )

    def test_resolve_path(self):
        pkg = self.make_package('foo')
        pkg.resolve(self.metadata)
        self.assertEqual(pkg.version(self.metadata), None)
        self.check_get_usage(pkg, None)
        self.check_pkg_config('foo', None)

    def test_resolve_pkg_config(self):
        pkg = self.make_package('foo')
        pkg.resolve(self.metadata)
        self.check_get_usage(pkg, None, {
            'name': 'foo', 'type': 'system', 'path': [], 'pcfiles': ['foo'],
            'extra_args': [],
        }, find_pkg_config=True)

    def test_explicit_version(self):
        pkg = self.make_package('foo', version='2.0')
        pkg.resolve(self.metadata)
        self.assertEqual(pkg.version(self.metadata), '2.0')
        self.check_get_usage(pkg, None)
        self.check_pkg_config('foo', None)

    def test_auto_link(self):
        pkg = self.make_package('foo', auto_link=True)
        pkg.resolve(self.metadata)
        self.check_get_usage(pkg, None, {
            'name': 'foo', 'type': 'system', 'generated': True,
            'auto_link': True, 'path': [self.pkgconfdir], 'pcfiles': ['foo'],
        })
        self.check_pkg_config('foo', None, {
            'libs': ['-L' + abspath('/mock/lib')],
        })

    def test_include_path(self):
        incdir = abspath('/mock/path/to/include')
        pkg = self.make_package('foo', include_path='/mock/path/to/include',
                                headers=['foo.hpp'])
        pkg.resolve(self.metadata)
        self.check_get_usage(pkg, None)
        self.check_pkg_config('foo', None, {'cflags': ['-I' + incdir]})

    def test_library_path(self):
        libdir = abspath('/mock/path/to/lib')
        pkg = self.make_package('foo', library_path='/mock/path/to/lib')
        pkg.resolve(self.metadata)
        self.check_get_usage(pkg, None)
        self.check_pkg_config('foo', None, {'libs': ['-L' + libdir, '-lfoo']})

    def test_headers(self):
        pkg = self.make_package('foo', headers='foo.hpp')
        pkg.resolve(self.metadata)
        self.check_get_usage(pkg, None)
        self.check_pkg_config('foo', None, {
            'cflags': ['-I' + abspath('/mock/include')],
        })

        pkg = self.make_package('foo', headers=['foo.hpp'])
        pkg.resolve(self.metadata)
        self.check_get_usage(pkg, None)
        self.check_pkg_config('foo', None, {
            'cflags': ['-I' + abspath('/mock/include')],
        })

    def test_libraries(self):
        pkg = self.make_package('foo', libraries='bar')
        pkg.resolve(self.metadata)
        self.check_get_usage(pkg, None)
        self.check_pkg_config('foo', None, {
            'libs': ['-L' + abspath('/mock/lib'), '-lbar'],
        })

        pkg = self.make_package('foo', libraries=['foo', 'bar'])
        pkg.resolve(self.metadata)
        self.check_get_usage(pkg, None)
        self.check_pkg_config('foo', None, {
            'libs': ['-L' + abspath('/mock/lib'), '-lfoo', '-lbar'],
        })

        pkg = self.make_package('foo', libraries=None)
        pkg.resolve(self.metadata)
        self.check_get_usage(pkg, None)
        self.check_pkg_config('foo', None, {'libs': []})

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        pkg = self.make_package('foo', submodules=submodules_required)
        self.check_get_usage(pkg, ['sub'])
        self.check_pkg_config('foo', ['sub'], {
            'libs': ['-L' + abspath('/mock/lib'), '-lfoo_sub'],
        })

        pkg = self.make_package('foo', libraries='bar',
                                submodules=submodules_required)
        self.check_get_usage(pkg, ['sub'])
        self.check_pkg_config('foo', ['sub'], {
            'libs': ['-L' + abspath('/mock/lib'), '-lbar', '-lfoo_sub'],
        })

        pkg = self.make_package('foo', submodules=submodules_optional)
        self.check_get_usage(pkg, ['sub'])
        self.check_pkg_config('foo', ['sub'], {
            'libs': ['-L' + abspath('/mock/lib'), '-lfoo', '-lfoo_sub'],
        })

        pkg = self.make_package('foo', libraries='bar',
                                submodules=submodules_optional)
        self.check_get_usage(pkg, ['sub'])
        self.check_pkg_config('foo', ['sub'], {
            'libs': ['-L' + abspath('/mock/lib'), '-lbar', '-lfoo_sub'],
        })

    def test_invalid_submodule(self):
        pkg = self.make_package('foo', submodules={
            'names': ['sub'], 'required': True
        })
        with self.assertRaises(ValueError):
            pkg.get_usage(self.metadata, ['invalid'])

    def test_invalid_usage(self):
        with self.assertRaises(FieldKeyError):
            self.make_package('foo', usage={'type': 'system'})

    def test_deploy(self):
        pkg = self.make_package('foo')
        # This is a no-op; just make sure it executes ok.
        pkg.deploy(self.metadata)

    def test_clean_pre(self):
        oldpkg = self.make_package('foo')
        newpkg = self.make_package(AptPackage, 'foo')

        # System -> Apt
        self.assertEqual(oldpkg.clean_pre(self.metadata, newpkg), False)

        # Apt -> nothing
        self.assertEqual(oldpkg.clean_pre(self.metadata, None), False)

    def test_clean_post(self):
        oldpkg = self.make_package('foo')
        newpkg = self.make_package(AptPackage, 'foo')

        # System -> Apt
        self.assertEqual(oldpkg.clean_post(self.metadata, newpkg), False)

        # Apt -> nothing
        self.assertEqual(oldpkg.clean_post(self.metadata, None), False)

    def test_clean_all(self):
        oldpkg = self.make_package('foo')
        newpkg = self.make_package(AptPackage, 'foo')

        # System -> Apt
        self.assertEqual(oldpkg.clean_all(self.metadata, newpkg),
                         (False, False))

        # Apt -> nothing
        self.assertEqual(oldpkg.clean_all(self.metadata, None), (False, False))

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

    def test_upgrade(self):
        opts = self.make_options()
        data = {'source': 'system', '_version': 0, 'name': 'foo',
                'usage': {'type': 'system', '_version': 0}}
        with mock.patch.object(SystemPackage, 'upgrade',
                               side_effect=SystemPackage.upgrade) as m:
            pkg = Package.rehydrate(data, _options=opts)
            self.assertIsInstance(pkg, SystemPackage)
            m.assert_called_once()
