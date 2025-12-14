import os
import subprocess
from unittest import mock

from . import MockPackage, through_json, LinkageTest
from .. import rehydrate_kwargs

from mopack.linkages import Linkage
from mopack.linkages.pkg_config import PkgConfigLinkage
from mopack.path import Path
from mopack.platforms import platform_name
from mopack.types import FieldError


class TestPkgConfig(LinkageTest):
    linkage_type = PkgConfigLinkage
    pkgconfdir = os.path.join(LinkageTest.builddir, 'pkgconfig')

    def test_basic(self):
        pkg = MockPackage(builddir=self.builddir)
        linkage = self.make_linkage('foo')
        self.assertEqual(linkage.pcname, 'foo')
        self.assertEqual(linkage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])

        with mock.patch('subprocess.run') as mrun:
            linkage.version(self.metadata, pkg)
            mrun.assert_called_once_with(
                ['pkg-config', 'foo', '--modversion'],
                check=True, env={'PKG_CONFIG_PATH': self.pkgconfdir},
                stdout=subprocess.PIPE, universal_newlines=True
            )

        self.assertEqual(
            linkage.get_linkage(self.metadata, pkg, None),
            {'name': 'foo', 'type': 'pkg_config', 'pcnames': ['foo'],
             'pkg_config_path': [self.pkgconfdir]}
        )

    def test_path_relative(self):
        pkg = MockPackage(srcdir=self.srcdir, builddir=self.builddir)
        linkage = self.make_linkage('foo', pkg_config_path='pkgconf')
        self.assertEqual(linkage.pcname, 'foo')
        self.assertEqual(linkage.pkg_config_path,
                         [Path('pkgconf', 'builddir')])
        self.assertEqual(
            linkage.get_linkage(self.metadata, pkg, None),
            {'name': 'foo', 'type': 'pkg_config', 'pcnames': ['foo'],
             'pkg_config_path': [os.path.join(self.builddir, 'pkgconf')]}
        )

    def test_path_srcdir(self):
        pkg = MockPackage(srcdir=self.srcdir, builddir=self.builddir)
        linkage = self.make_linkage('foo', pkg_config_path='$srcdir/pkgconf')
        self.assertEqual(linkage.pcname, 'foo')
        self.assertEqual(linkage.pkg_config_path, [Path('pkgconf', 'srcdir')])
        self.assertEqual(
            linkage.get_linkage(self.metadata, pkg, None),
            {'name': 'foo', 'type': 'pkg_config', 'pcnames': ['foo'],
             'pkg_config_path': [os.path.join(self.srcdir, 'pkgconf')]}
        )

    def test_path_builddir(self):
        pkg = MockPackage(srcdir=self.srcdir, builddir=self.builddir)
        linkage = self.make_linkage('foo', pkg_config_path='$builddir/pkgconf')
        self.assertEqual(linkage.pcname, 'foo')
        self.assertEqual(linkage.pkg_config_path,
                         [Path('pkgconf', 'builddir')])
        self.assertEqual(
            linkage.get_linkage(self.metadata, pkg, None),
            {'name': 'foo', 'type': 'pkg_config', 'pcnames': ['foo'],
             'pkg_config_path': [os.path.join(self.builddir, 'pkgconf')]}
        )

    def test_submodules(self):
        pkg = MockPackage(builddir=self.builddir)

        linkage = self.make_linkage('foo', submodules='*',
                                    submodule_required=True)
        self.assertEqual(linkage.pcname, None)
        self.assertEqual(linkage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])
        self.assertEqual(
            linkage.get_linkage(self.metadata, pkg, ['sub']),
            {'name': 'foo[sub]', 'type': 'pkg_config', 'pcnames': ['foo_sub'],
             'pkg_config_path': [self.pkgconfdir]}
        )

        linkage = self.make_linkage('foo', pcname='bar', submodules='*',
                                    submodule_required=True)
        self.assertEqual(linkage.pcname, 'bar')
        self.assertEqual(linkage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])
        self.assertEqual(
            linkage.get_linkage(self.metadata, pkg, ['sub']),
            {'name': 'foo[sub]', 'type': 'pkg_config',
             'pcnames': ['bar', 'foo_sub'],
             'pkg_config_path': [self.pkgconfdir]}
        )

        linkage = self.make_linkage('foo', submodules='*',
                                    submodule_required=False)
        self.assertEqual(linkage.pcname, 'foo')
        self.assertEqual(linkage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])
        self.assertEqual(
            linkage.get_linkage(self.metadata, pkg, ['sub']),
            {'name': 'foo[sub]', 'type': 'pkg_config',
             'pcnames': ['foo', 'foo_sub'],
             'pkg_config_path': [self.pkgconfdir]}
        )

        linkage = self.make_linkage('foo', pcname='bar', submodules='*',
                                    submodule_required=False)
        self.assertEqual(linkage.pcname, 'bar')
        self.assertEqual(linkage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])
        self.assertEqual(
            linkage.get_linkage(self.metadata, pkg, ['sub']),
            {'name': 'foo[sub]', 'type': 'pkg_config',
             'pcnames': ['bar', 'foo_sub'],
             'pkg_config_path': [self.pkgconfdir]}
        )

    def test_submodule_linkage(self):
        pkg = MockPackage('foo', builddir=self.builddir, submodules='*',
                          submodule_required=True)

        linkage = self.make_linkage(pkg, submodule_linkage='$submodule')
        self.assertEqual(linkage.pcname, None)
        self.assertEqual(linkage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])
        self.assertEqual(
            linkage.get_linkage(self.metadata, pkg, ['sub']),
            {'name': 'foo[sub]', 'type': 'pkg_config', 'pcnames': ['sub'],
             'pkg_config_path': [self.pkgconfdir]}
        )

        linkage = self.make_linkage(pkg, submodule_linkage={
            'pcname': '$submodule'
        })
        self.assertEqual(linkage.pcname, None)
        self.assertEqual(linkage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])
        self.assertEqual(
            linkage.get_linkage(self.metadata, pkg, ['sub']),
            {'name': 'foo[sub]', 'type': 'pkg_config', 'pcnames': ['sub'],
             'pkg_config_path': [self.pkgconfdir]}
        )

        linkage = self.make_linkage(pkg, submodule_linkage={
            'pcname': '${{ submodule + "_" + target_platform }}'
        })
        self.assertEqual(linkage.pcname, None)
        self.assertEqual(linkage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])
        self.assertEqual(
            linkage.get_linkage(self.metadata, pkg, ['sub']),
            {'name': 'foo[sub]', 'type': 'pkg_config',
             'pcnames': ['sub_' + platform_name()],
             'pkg_config_path': [self.pkgconfdir]}
        )

        linkage = self.make_linkage(pkg, submodule_linkage=[
            {'if': 'submodule == "sub"',
             'pcname': 'foopc'},
            {'if': 'submodule == "sub2"',
             'pcname': '${{ submodule }}pc'},
            {'pcname': 'star${{ submodule }}pc'},
        ])
        self.assertEqual(linkage.pcname, None)
        self.assertEqual(linkage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])
        self.assertEqual(
            linkage.get_linkage(self.metadata, pkg, ['sub']),
            {'name': 'foo[sub]', 'type': 'pkg_config', 'pcnames': ['foopc'],
             'pkg_config_path': [self.pkgconfdir]}
        )
        self.assertEqual(
            linkage.get_linkage(self.metadata, pkg, ['sub2']),
            {'name': 'foo[sub2]', 'type': 'pkg_config', 'pcnames': ['sub2pc'],
             'pkg_config_path': [self.pkgconfdir]}
        )
        self.assertEqual(
            linkage.get_linkage(self.metadata, pkg, ['subfoo']),
            {'name': 'foo[subfoo]', 'type': 'pkg_config',
             'pcnames': ['starsubfoopc'], 'pkg_config_path': [self.pkgconfdir]}
        )

        pkg = MockPackage('foo', builddir=self.builddir, submodules='*',
                          submodule_required=False)

        linkage = self.make_linkage(pkg, submodule_linkage=[
            {'if': 'submodule == "sub"', 'pcname': 'subpc'},
            {'if': 'submodule == "sub2"', 'pcname': None},
        ])
        self.assertEqual(linkage.pcname, 'foo')
        self.assertEqual(linkage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])
        self.assertEqual(
            linkage.get_linkage(self.metadata, pkg, ['sub']),
            {'name': 'foo[sub]', 'type': 'pkg_config',
             'pcnames': ['foo', 'subpc'], 'pkg_config_path': [self.pkgconfdir]}
        )
        self.assertEqual(
            linkage.get_linkage(self.metadata, pkg, ['sub2']),
            {'name': 'foo[sub2]', 'type': 'pkg_config', 'pcnames': ['foo'],
             'pkg_config_path': [self.pkgconfdir]}
        )

    def test_boost(self):
        pkg = MockPackage('boost', builddir=self.builddir, submodules='*',
                          submodule_required=False)

        linkage = self.make_linkage(pkg, inherit_defaults=True)
        self.assertEqual(linkage.pcname, 'boost')
        self.assertEqual(linkage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])
        self.assertEqual(
            linkage.get_linkage(self.metadata, pkg, None),
            {'name': 'boost', 'type': 'pkg_config', 'pcnames': ['boost'],
             'pkg_config_path': [self.pkgconfdir]}
        )
        self.assertEqual(
            linkage.get_linkage(self.metadata, pkg, ['thread']),
            {'name': 'boost[thread]', 'type': 'pkg_config',
             'pcnames': ['boost'], 'pkg_config_path': [self.pkgconfdir]}
        )

        linkage = self.make_linkage(pkg, inherit_defaults=True,
                                    submodule_linkage='boost_$submodule')
        self.assertEqual(linkage.pcname, 'boost')
        self.assertEqual(linkage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])
        self.assertEqual(
            linkage.get_linkage(self.metadata, pkg, None),
            {'name': 'boost', 'type': 'pkg_config', 'pcnames': ['boost'],
             'pkg_config_path': [self.pkgconfdir]}
        )
        self.assertEqual(
            linkage.get_linkage(self.metadata, pkg, ['thread']),
            {'name': 'boost[thread]', 'type': 'pkg_config',
             'pcnames': ['boost', 'boost_thread'],
             'pkg_config_path': [self.pkgconfdir]}
        )

    def test_rehydrate(self):
        opts = self.make_options()
        symbols = opts.expr_symbols.augment(path_bases=['builddir'])
        pkg = MockPackage('foo', srcdir=self.srcdir, builddir=self.builddir,
                          _options=opts)
        linkage = PkgConfigLinkage(pkg, _symbols=symbols)
        data = through_json(linkage.dehydrate())
        self.assertEqual(linkage, Linkage.rehydrate(
            data, name=pkg.name, _options=opts, _symbols=symbols,
            **rehydrate_kwargs
        ))

        linkage = PkgConfigLinkage(pkg, pcname='foopc', _symbols=symbols)
        data = through_json(linkage.dehydrate())
        self.assertEqual(linkage, Linkage.rehydrate(
            data, name=pkg.name, _options=opts, _symbols=symbols,
            **rehydrate_kwargs
        ))

    def test_upgrade(self):
        opts = self.make_options()
        symbols = opts.expr_symbols.augment(path_bases=['builddir'])
        data = {
            'type': 'pkg_config', '_version': 1, 'pcname': 'foo',
            'submodule_map': {
                'sub': {'pcname': 'sub'},
                '*': {'pcname': 'star$submodule'},
            }
        }
        with mock.patch.object(PkgConfigLinkage, 'upgrade',
                               side_effect=PkgConfigLinkage.upgrade) as m:
            linkage = Linkage.rehydrate(data, name='foo', _options=opts,
                                        _symbols=symbols, **rehydrate_kwargs)
            self.assertIsInstance(linkage, PkgConfigLinkage)
            self.assertEqual([i._if for i in linkage.submodule_linkage],
                             ["submodule == 'sub'", True])
            self.assertEqual([i.pcname for i in linkage.submodule_linkage],
                             ['sub', 'star$submodule'])

            m.assert_called_once()

    def test_invalid_linkage(self):
        opts = self.make_options()
        pkg = MockPackage('foo', builddir=self.builddir, _options=opts)
        with self.assertRaises(FieldError):
            self.make_linkage(pkg, pkg_config_path='$srcdir/pkgconf')

        pkg = MockPackage('foo', srcdir=self.srcdir, _options=opts)
        with self.assertRaises(FieldError):
            self.make_linkage(pkg, pkg_config_path='$builddir/pkgconf')

        pkg = MockPackage('foo', _options=opts)
        with self.assertRaises(FieldError):
            self.make_linkage(pkg)
