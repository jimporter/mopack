import os
import shutil
from unittest import mock

from . import SourceTest
from ... import call_pkg_config, test_stage_dir

from mopack.iterutils import iterate
from mopack.sources import Package
from mopack.sources.apt import AptPackage
from mopack.sources.system import SystemPackage


class TestSystemPackage(SourceTest):
    pkg_type = SystemPackage
    config_file = os.path.abspath('/path/to/mopack.yml')
    pkgdir = os.path.join(test_stage_dir, 'sources')
    pkgconfdir = os.path.join(pkgdir, 'pkgconfig')

    def setUp(self):
        self.clear_pkgdir()

    def clear_pkgdir(self):
        if os.path.exists(self.pkgdir):
            shutil.rmtree(self.pkgdir)

    def check_get_usage(self, pkg, submodules, expected=None, *,
                        find_pkg_config=False):
        pcname = ('{}[{}]'.format(pkg.name, ','.join(iterate(submodules)))
                  if submodules else pkg.name)
        if expected is None:
            expected = {
                'name': pkg.name, 'type': 'system', 'path': self.pkgconfdir,
                'pcfiles': [pcname], 'requirements': {
                    'auto_link': False, 'headers': [], 'libraries': [pkg.name],
                },
            }

        self.clear_pkgdir()
        side_effect = None if find_pkg_config else OSError()
        with mock.patch('subprocess.run', side_effect=side_effect), \
             mock.patch('mopack.usage.path_system.file_outdated',
                        return_value=True):  # noqa
            self.assertEqual(pkg.get_usage(submodules, self.pkgdir), expected)

    def check_pkg_config(self, name, submodules, expected={}):
        pcname = ('{}[{}]'.format(name, ','.join(iterate(submodules)))
                  if submodules else name)
        self.assertCountEqual(
            call_pkg_config(pcname, ['--cflags'], path=self.pkgconfdir),
            expected.get('cflags', [])
        )
        self.assertCountEqual(
            call_pkg_config(pcname, ['--libs'], path=self.pkgconfdir),
            expected.get('libs', ['-l' + name])
        )

    def test_resolve_path(self):
        pkg = self.make_package('foo')
        pkg.resolve(self.pkgdir)
        self.check_get_usage(pkg, None)
        self.check_pkg_config('foo', None)

    def test_resolve_pkg_config(self):
        pkg = self.make_package('foo')
        pkg.resolve(self.pkgdir)
        self.check_get_usage(pkg, None, {
            'name': 'foo', 'type': 'system', 'path': None, 'pcfiles': ['foo'],
            'extra_args': [],
        }, find_pkg_config=True)

    def test_auto_link(self):
        pkg = self.make_package('foo', auto_link=True)
        pkg.resolve(self.pkgdir)
        self.check_get_usage(pkg, None, {
            'name': 'foo', 'type': 'system', 'path': self.pkgconfdir,
            'pcfiles': ['foo'], 'requirements': {
                'auto_link': True, 'headers': [], 'libraries': ['foo'],
            },
        })
        self.check_pkg_config('foo', None)

    def test_include_path(self):
        incdir = os.path.abspath('/path/to/include')
        pkg = self.make_package('foo', include_path='/path/to/include')
        pkg.resolve(self.pkgdir)
        self.check_get_usage(pkg, None, {
            'name': 'foo', 'type': 'system', 'path': self.pkgconfdir,
            'pcfiles': ['foo'], 'requirements': {
                'auto_link': False, 'headers': [], 'libraries': ['foo'],
            },
        })
        self.check_pkg_config('foo', None, {'cflags': ['-I' + incdir]})

    def test_library_path(self):
        libdir = os.path.abspath('/path/to/lib')
        pkg = self.make_package('foo', library_path='/path/to/lib')
        pkg.resolve(self.pkgdir)
        self.check_get_usage(pkg, None, {
            'name': 'foo', 'type': 'system', 'path': self.pkgconfdir,
            'pcfiles': ['foo'], 'requirements': {
                'auto_link': False, 'headers': [], 'libraries': ['foo'],
            },
        })
        self.check_pkg_config('foo', None, {
            'libs': ['-L' + libdir, '-lfoo'],
        })

    def test_headers(self):
        pkg = self.make_package('foo', headers='foo.hpp')
        pkg.resolve(self.pkgdir)
        self.check_get_usage(pkg, None, {
            'name': 'foo', 'type': 'system', 'path': self.pkgconfdir,
            'pcfiles': ['foo'], 'requirements': {
                'auto_link': False, 'headers': ['foo.hpp'],
                'libraries': ['foo'],
            },
        })
        self.check_pkg_config('foo', None)

        pkg = self.make_package('foo', headers=['foo.hpp', 'bar.hpp'])
        pkg.resolve(self.pkgdir)
        self.check_get_usage(pkg, None, {
            'name': 'foo', 'type': 'system', 'path': self.pkgconfdir,
            'pcfiles': ['foo'], 'requirements': {
                'auto_link': False, 'headers': ['foo.hpp', 'bar.hpp'],
                'libraries': ['foo'],
            },
        })
        self.check_pkg_config('foo', None)

    def test_libraries(self):
        pkg = self.make_package('foo', libraries='bar')
        pkg.resolve(self.pkgdir)
        self.check_get_usage(pkg, None, {
            'name': 'foo', 'type': 'system', 'path': self.pkgconfdir,
            'pcfiles': ['foo'], 'requirements': {
                'auto_link': False, 'headers': [], 'libraries': ['bar'],
            },
        })
        self.check_pkg_config('foo', None, {'libs': ['-lbar']})

        pkg = self.make_package('foo', libraries=['foo', 'bar'])
        pkg.resolve(self.pkgdir)
        self.check_get_usage(pkg, None, {
            'name': 'foo', 'type': 'system', 'path': self.pkgconfdir,
            'pcfiles': ['foo'], 'requirements': {
                'auto_link': False, 'headers': [], 'libraries': ['foo', 'bar'],
            },
        })
        self.check_pkg_config('foo', None, {'libs': ['-lfoo', '-lbar']})

        pkg = self.make_package('foo', libraries=None)
        pkg.resolve(self.pkgdir)
        self.check_get_usage(pkg, None, {
            'name': 'foo', 'type': 'system', 'path': self.pkgconfdir,
            'pcfiles': ['foo'], 'requirements': {
                'auto_link': False, 'headers': [], 'libraries': [],
            },
        })
        self.check_pkg_config('foo', None, {'libs': []})

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        pkg = self.make_package('foo', submodules=submodules_required)
        self.check_get_usage(pkg, 'sub', {
            'name': 'foo', 'type': 'system', 'path': self.pkgconfdir,
            'pcfiles': ['foo[sub]'], 'requirements': {
                'auto_link': False, 'headers': [], 'libraries': ['foo_sub'],
            },
        })
        self.check_pkg_config('foo', ['sub'], {'libs': ['-lfoo_sub']})

        pkg = self.make_package('foo', libraries='bar',
                                submodules=submodules_required)
        self.check_get_usage(pkg, 'sub', {
            'name': 'foo', 'type': 'system', 'path': self.pkgconfdir,
            'pcfiles': ['foo[sub]'], 'requirements': {
                'auto_link': False, 'headers': [],
                'libraries': ['bar', 'foo_sub'],
            },
        })
        self.check_pkg_config('foo', ['sub'], {'libs': ['-lbar', '-lfoo_sub']})

        pkg = self.make_package('foo', submodules=submodules_optional)
        self.check_get_usage(pkg, 'sub', {
            'name': 'foo', 'type': 'system', 'path': self.pkgconfdir,
            'pcfiles': ['foo[sub]'], 'requirements': {
                'auto_link': False, 'headers': [],
                'libraries': ['foo', 'foo_sub'],
            },
        })
        self.check_pkg_config('foo', ['sub'], {'libs': ['-lfoo', '-lfoo_sub']})

        pkg = self.make_package('foo', libraries='bar',
                                submodules=submodules_optional)
        self.check_get_usage(pkg, 'sub', {
            'name': 'foo', 'type': 'system', 'path': self.pkgconfdir,
            'pcfiles': ['foo[sub]'], 'requirements': {
                'auto_link': False, 'headers': [],
                'libraries': ['bar', 'foo_sub'],
            },
        })
        self.check_pkg_config('foo', ['sub'], {'libs': ['-lbar', '-lfoo_sub']})

    def test_invalid_submodule(self):
        pkg = self.make_package('foo', submodules={
            'names': ['sub'], 'required': True
        })
        with self.assertRaises(ValueError):
            pkg.get_usage(['invalid'], self.pkgdir)

    def test_deploy(self):
        pkg = self.make_package('foo')
        # This is a no-op; just make sure it executes ok.
        pkg.deploy(self.pkgdir)

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

    def test_upgrade(self):
        opts = self.make_options()
        data = {'source': 'system', '_version': 0, 'name': 'foo',
                'usage': {'type': 'system', '_version': 0}}
        with mock.patch.object(SystemPackage, 'upgrade',
                               side_effect=SystemPackage.upgrade) as m:
            pkg = Package.rehydrate(data, _options=opts)
            self.assertIsInstance(pkg, SystemPackage)
            m.assert_called_once()
