from . import SourceTest

from mopack.sources import Package, ResolvedPackage
from mopack.sources.apt import AptPackage
from mopack.sources.system import SystemPackage


class TestSystemPackage(SourceTest):
    pkg_type = SystemPackage
    config_file = '/path/to/mopack.yml'
    pkgdir = '/path/to/builddir/mopack'
    deploy_paths = {'prefix': '/usr/local'}

    def test_basic(self):
        pkg = self.make_package('foo')

        info = SystemPackage.resolve_all(self.pkgdir, [pkg], self.deploy_paths)
        self.assertEqual(info, [
            ResolvedPackage(pkg, {'type': 'system'}),
        ])

    def test_multiple(self):
        pkg1 = self.make_package('foo')
        pkg2 = self.make_package('bar')

        info = SystemPackage.resolve_all(self.pkgdir, [pkg1, pkg2],
                                         self.deploy_paths)
        self.assertEqual(info, [
            ResolvedPackage(pkg1, {'type': 'system'}),
            ResolvedPackage(pkg2, {'type': 'system'}),
        ])

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
        pkg = SystemPackage('foo', config_file=self.config_file)
        data = pkg.dehydrate()
        self.assertEqual(pkg, Package.rehydrate(data))
