import os
from unittest import mock

from . import SourceTest
from .. import mock_open_log

from mopack.iterutils import iterate
from mopack.sources import Package
from mopack.sources.apt import AptPackage
from mopack.sources.conan import ConanPackage


class TestApt(SourceTest):
    pkg_type = AptPackage
    config_file = '/path/to/mopack.yml'
    pkgdir = '/path/to/builddir/mopack'
    deploy_paths = {'prefix': '/usr/local'}

    def check_resolve_all(self, packages, remotes, *, submodules=None,
                          usages=None):
        with mock_open_log() as mopen, \
             mock.patch('subprocess.check_call') as mcall:  # noqa
            AptPackage.resolve_all(self.pkgdir, packages, self.deploy_paths)

            mopen.assert_called_with(os.path.join(self.pkgdir, 'apt.log'), 'w')
            mcall.assert_called_with(
                ['sudo', 'apt-get', 'install', '-y'] + remotes,
                stdout=mopen(), stderr=mopen()
            )

        if usages is None:
            usages = []
            for pkg in packages:
                libs = ([] if pkg.submodules and pkg.submodules['required']
                        else [pkg.name])
                libs.extend('{}_{}'.format(pkg.name, i)
                            for i in iterate(submodules))
                usages.append({
                    'type': 'system', 'include_path': [], 'library_path': [],
                    'headers': [], 'libraries': libs,
                })

        for pkg, usage in zip(packages, usages):
            self.assertEqual(pkg.get_usage(self.pkgdir, submodules), usage)

    def test_basic(self):
        pkg = self.make_package('foo')
        self.assertEqual(pkg.remote, 'libfoo-dev')
        self.check_resolve_all([pkg], ['libfoo-dev'])

    def test_remote(self):
        pkg = self.make_package('foo', remote='foo-dev')
        self.assertEqual(pkg.remote, 'foo-dev')
        self.check_resolve_all([pkg], ['foo-dev'])

    def test_multiple(self):
        pkg1 = self.make_package('foo')
        pkg2 = self.make_package('bar', remote='bar-dev')
        self.check_resolve_all([pkg1, pkg2], ['libfoo-dev', 'bar-dev'])

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        pkg = self.make_package('foo', submodules=submodules_required)
        self.check_resolve_all([pkg], ['libfoo-dev'], submodules=['sub'])

        pkg = self.make_package(
            'foo', usage={'type': 'system', 'libraries': 'bar'},
            submodules=submodules_required
        )
        self.check_resolve_all(
            [pkg], ['libfoo-dev'], submodules=['sub'], usages=[{
                'type': 'system', 'include_path': [], 'library_path': [],
                'headers': [], 'libraries': ['bar', 'foo_sub'],
            }]
        )

        pkg = self.make_package('foo', submodules=submodules_optional)
        self.check_resolve_all([pkg], ['libfoo-dev'], submodules=['sub'])

        pkg = self.make_package(
            'foo', usage={'type': 'system', 'libraries': 'bar'},
            submodules=submodules_optional
        )
        self.check_resolve_all(
            [pkg], ['libfoo-dev'], submodules=['sub'], usages=[{
                'type': 'system', 'include_path': [], 'library_path': [],
                'headers': [], 'libraries': ['bar', 'foo_sub'],
            }]
        )

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
        newpkg = self.make_package(ConanPackage, 'foo',
                                   remote='foo/1.2.4@conan/stable')

        # Apt -> Conan
        self.assertEqual(oldpkg.clean_pre(self.pkgdir, newpkg), False)

        # Apt -> nothing
        self.assertEqual(oldpkg.clean_pre(self.pkgdir, None), False)

    def test_clean_post(self):
        oldpkg = self.make_package('foo')
        newpkg = self.make_package(ConanPackage, 'foo',
                                   remote='foo/1.2.4@conan/stable')

        # Apt -> Conan
        self.assertEqual(oldpkg.clean_post(self.pkgdir, newpkg), False)

        # Apt -> nothing
        self.assertEqual(oldpkg.clean_post(self.pkgdir, None), False)

    def test_clean_all(self):
        oldpkg = self.make_package('foo')
        newpkg = self.make_package(ConanPackage, 'foo',
                                   remote='foo/1.2.4@conan/stable')

        # Apt -> Conan
        self.assertEqual(oldpkg.clean_all(self.pkgdir, newpkg), (False, False))

        # Apt -> nothing
        self.assertEqual(oldpkg.clean_all(self.pkgdir, None), (False, False))

    def test_equality(self):
        pkg = self.make_package('foo')

        self.assertEqual(pkg, self.make_package('foo'))
        self.assertEqual(pkg, self.make_package('foo', remote='libfoo-dev'))
        self.assertEqual(pkg, self.make_package(
            'foo', config_file='/path/to/mopack2.yml'
        ))

        self.assertNotEqual(pkg, self.make_package('bar'))
        self.assertNotEqual(pkg, self.make_package('bar', remote='libfoo-dev'))
        self.assertNotEqual(pkg, self.make_package('foo', remote='libbar-dev'))

    def test_rehydrate(self):
        pkg = AptPackage('foo', remote='libbar-dev',
                         config_file=self.config_file)
        data = pkg.dehydrate()
        self.assertEqual(pkg, Package.rehydrate(data))
