import os
from unittest import mock

from . import SourceTest
from .. import mock_open_log

from mopack.sources import Package, ResolvedPackage
from mopack.sources.apt import AptPackage
from mopack.sources.conan import ConanPackage


class TestApt(SourceTest):
    pkg_type = AptPackage
    config_file = '/path/to/mopack.yml'
    pkgdir = '/path/to/builddir/mopack'
    deploy_paths = {'prefix': '/usr/local'}

    def check_resolve_all(self, packages, remotes):
        with mock_open_log() as mopen, \
             mock.patch('subprocess.check_call') as mcall:  # noqa
            info = AptPackage.resolve_all(self.pkgdir, packages,
                                          self.deploy_paths)
            self.assertEqual(info, [ResolvedPackage(i, {'type': 'system'})
                                    for i in packages])

            mopen.assert_called_with(os.path.join(self.pkgdir, 'apt.log'), 'w')
            mcall.assert_called_with(
                ['sudo', 'apt-get', 'install', '-y'] + remotes,
                stdout=mopen(), stderr=mopen()
            )

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
