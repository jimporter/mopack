import os
import subprocess
from unittest import mock

from . import MockPackage, through_json, UsageTest

from mopack.path import Path
from mopack.types import FieldError
from mopack.usage import Usage
from mopack.usage.pkg_config import PkgConfigUsage


class TestPkgConfig(UsageTest):
    usage_type = PkgConfigUsage
    pkgconfdir = os.path.join(UsageTest.builddir, 'pkgconfig')

    def test_basic(self):
        pkg = MockPackage(builddir=self.builddir)
        usage = self.make_usage('foo')
        self.assertEqual(usage.pcname, 'foo')
        self.assertEqual(usage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])

        with mock.patch('subprocess.run') as mrun:
            usage.version(self.metadata, pkg)
            mrun.assert_called_once_with(
                ['pkg-config', 'foo', '--modversion'],
                check=True, env={'PKG_CONFIG_PATH': self.pkgconfdir},
                stdout=subprocess.PIPE, universal_newlines=True
            )

        self.assertEqual(
            usage.get_usage(self.metadata, pkg, None),
            {'name': 'foo', 'type': 'pkg_config', 'pcnames': ['foo'],
             'pkg_config_path': [self.pkgconfdir]}
        )

    def test_path_relative(self):
        pkg = MockPackage(srcdir=self.srcdir, builddir=self.builddir)
        usage = self.make_usage('foo', pkg_config_path='pkgconf')
        self.assertEqual(usage.pcname, 'foo')
        self.assertEqual(usage.pkg_config_path, [Path('pkgconf', 'builddir')])
        self.assertEqual(
            usage.get_usage(self.metadata, pkg, None),
            {'name': 'foo', 'type': 'pkg_config', 'pcnames': ['foo'],
             'pkg_config_path': [os.path.join(self.builddir, 'pkgconf')]}
        )

    def test_path_srcdir(self):
        pkg = MockPackage(srcdir=self.srcdir, builddir=self.builddir)
        usage = self.make_usage('foo', pkg_config_path='$srcdir/pkgconf')
        self.assertEqual(usage.pcname, 'foo')
        self.assertEqual(usage.pkg_config_path, [Path('pkgconf', 'srcdir')])
        self.assertEqual(
            usage.get_usage(self.metadata, pkg, None),
            {'name': 'foo', 'type': 'pkg_config', 'pcnames': ['foo'],
             'pkg_config_path': [os.path.join(self.srcdir, 'pkgconf')]}
        )

    def test_path_builddir(self):
        pkg = MockPackage(srcdir=self.srcdir, builddir=self.builddir)
        usage = self.make_usage('foo', pkg_config_path='$builddir/pkgconf')
        self.assertEqual(usage.pcname, 'foo')
        self.assertEqual(usage.pkg_config_path, [Path('pkgconf', 'builddir')])
        self.assertEqual(
            usage.get_usage(self.metadata, pkg, None),
            {'name': 'foo', 'type': 'pkg_config', 'pcnames': ['foo'],
             'pkg_config_path': [os.path.join(self.builddir, 'pkgconf')]}
        )

    def test_submodules(self):
        pkg = MockPackage(builddir=self.builddir)
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        usage = self.make_usage('foo', submodules=submodules_required)
        self.assertEqual(usage.pcname, None)
        self.assertEqual(usage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])
        self.assertEqual(
            usage.get_usage(self.metadata, pkg, ['sub']),
            {'name': 'foo[sub]', 'type': 'pkg_config', 'pcnames': ['foo_sub'],
             'pkg_config_path': [self.pkgconfdir]}
        )

        usage = self.make_usage('foo', pcname='bar',
                                submodules=submodules_required)
        self.assertEqual(usage.pcname, 'bar')
        self.assertEqual(usage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])
        self.assertEqual(
            usage.get_usage(self.metadata, pkg, ['sub']),
            {'name': 'foo[sub]', 'type': 'pkg_config',
             'pcnames': ['bar', 'foo_sub'],
             'pkg_config_path': [self.pkgconfdir]}
        )

        usage = self.make_usage('foo', submodules=submodules_optional)
        self.assertEqual(usage.pcname, 'foo')
        self.assertEqual(usage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])
        self.assertEqual(
            usage.get_usage(self.metadata, pkg, ['sub']),
            {'name': 'foo[sub]', 'type': 'pkg_config',
             'pcnames': ['foo', 'foo_sub'],
             'pkg_config_path': [self.pkgconfdir]}
        )

        usage = self.make_usage('foo', pcname='bar',
                                submodules=submodules_optional)
        self.assertEqual(usage.pcname, 'bar')
        self.assertEqual(usage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])
        self.assertEqual(
            usage.get_usage(self.metadata, pkg, ['sub']),
            {'name': 'foo[sub]', 'type': 'pkg_config',
             'pcnames': ['bar', 'foo_sub'],
             'pkg_config_path': [self.pkgconfdir]}
        )

    def test_submodule_map(self):
        pkg = MockPackage(builddir=self.builddir)
        submodules_required = {'names': '*', 'required': True}

        usage = self.make_usage('foo', submodule_map='$submodule',
                                submodules=submodules_required)
        self.assertEqual(usage.pcname, None)
        self.assertEqual(usage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])
        self.assertEqual(
            usage.get_usage(self.metadata, pkg, ['sub']),
            {'name': 'foo[sub]', 'type': 'pkg_config', 'pcnames': ['sub'],
             'pkg_config_path': [self.pkgconfdir]}
        )

        usage = self.make_usage('foo', submodule_map={
            '*': {'pcname': '$submodule'}
        }, submodules=submodules_required)
        self.assertEqual(usage.pcname, None)
        self.assertEqual(usage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])
        self.assertEqual(
            usage.get_usage(self.metadata, pkg, ['sub']),
            {'name': 'foo[sub]', 'type': 'pkg_config', 'pcnames': ['sub'],
             'pkg_config_path': [self.pkgconfdir]}
        )

        usage = self.make_usage('foo', submodule_map={
            'sub': {'pcname': 'foopc'},
            'sub2': {'pcname': '${{ submodule }}pc'},
            '*': {'pcname': 'star${{ submodule }}pc'},
        }, submodules=submodules_required)
        self.assertEqual(usage.pcname, None)
        self.assertEqual(usage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])
        self.assertEqual(
            usage.get_usage(self.metadata, pkg, ['sub']),
            {'name': 'foo[sub]', 'type': 'pkg_config', 'pcnames': ['foopc'],
             'pkg_config_path': [self.pkgconfdir]}
        )
        self.assertEqual(
            usage.get_usage(self.metadata, pkg, ['sub2']),
            {'name': 'foo[sub2]', 'type': 'pkg_config', 'pcnames': ['sub2pc'],
             'pkg_config_path': [self.pkgconfdir]}
        )
        self.assertEqual(
            usage.get_usage(self.metadata, pkg, ['subfoo']),
            {'name': 'foo[subfoo]', 'type': 'pkg_config',
             'pcnames': ['starsubfoopc'], 'pkg_config_path': [self.pkgconfdir]}
        )

        submodules = {'names': '*', 'required': False}
        usage = self.make_usage('foo', submodule_map={
            'sub': {'pcname': 'subpc'},
            'sub2': {'pcname': None},
        }, submodules=submodules)
        self.assertEqual(usage.pcname, 'foo')
        self.assertEqual(usage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])
        self.assertEqual(
            usage.get_usage(self.metadata, pkg, ['sub']),
            {'name': 'foo[sub]', 'type': 'pkg_config',
             'pcnames': ['foo', 'subpc'], 'pkg_config_path': [self.pkgconfdir]}
        )
        self.assertEqual(
            usage.get_usage(self.metadata, pkg, ['sub2']),
            {'name': 'foo[sub2]', 'type': 'pkg_config', 'pcnames': ['foo'],
             'pkg_config_path': [self.pkgconfdir]}
        )

    def test_boost(self):
        pkg = MockPackage('boost', builddir=self.builddir)
        submodules = {'names': '*', 'required': False}

        usage = self.make_usage('boost', inherit_defaults=True,
                                submodules=submodules)
        self.assertEqual(usage.pcname, 'boost')
        self.assertEqual(usage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])
        self.assertEqual(
            usage.get_usage(self.metadata, pkg, None),
            {'name': 'boost', 'type': 'pkg_config', 'pcnames': ['boost'],
             'pkg_config_path': [self.pkgconfdir]}
        )
        self.assertEqual(
            usage.get_usage(self.metadata, pkg, ['thread']),
            {'name': 'boost[thread]', 'type': 'pkg_config',
             'pcnames': ['boost'], 'pkg_config_path': [self.pkgconfdir]}
        )

        usage = self.make_usage('boost', inherit_defaults=True,
                                submodule_map='boost_$submodule',
                                submodules=submodules)
        self.assertEqual(usage.pcname, 'boost')
        self.assertEqual(usage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])
        self.assertEqual(
            usage.get_usage(self.metadata, pkg, None),
            {'name': 'boost', 'type': 'pkg_config', 'pcnames': ['boost'],
             'pkg_config_path': [self.pkgconfdir]}
        )
        self.assertEqual(
            usage.get_usage(self.metadata, pkg, ['thread']),
            {'name': 'boost[thread]', 'type': 'pkg_config',
             'pcnames': ['boost', 'boost_thread'],
             'pkg_config_path': [self.pkgconfdir]}
        )

    def test_rehydrate(self):
        opts = self.make_options()
        pkg = MockPackage('foo', srcdir=self.srcdir, builddir=self.builddir,
                          _options=opts)
        usage = PkgConfigUsage(pkg)
        data = through_json(usage.dehydrate())
        self.assertEqual(usage, Usage.rehydrate(data, _options=opts))

        usage = PkgConfigUsage(pkg, pcname='foopc')
        data = through_json(usage.dehydrate())
        self.assertEqual(usage, Usage.rehydrate(data, _options=opts))

    def test_upgrade(self):
        opts = self.make_options()
        data = {'type': 'pkg_config', '_version': 0, 'pcname': 'foo'}
        with mock.patch.object(PkgConfigUsage, 'upgrade',
                               side_effect=PkgConfigUsage.upgrade) as m:
            pkg = Usage.rehydrate(data, _options=opts)
            self.assertIsInstance(pkg, PkgConfigUsage)
            m.assert_called_once()

    def test_invalid_usage(self):
        opts = self.make_options()
        pkg = MockPackage('foo', builddir=self.builddir, _options=opts)
        with self.assertRaises(FieldError):
            self.make_usage(pkg, pkg_config_path='$srcdir/pkgconf')

        pkg = MockPackage('foo', srcdir=self.srcdir, _options=opts)
        with self.assertRaises(FieldError):
            self.make_usage(pkg, pkg_config_path='$builddir/pkgconf')

        pkg = MockPackage('foo', _options=opts)
        with self.assertRaises(FieldError):
            self.make_usage(pkg)
