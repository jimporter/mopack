from unittest import TestCase

from mopack.sources import Package
from mopack.sources.apt import AptPackage
from mopack.sources.system import SystemPackage


class TestSystemPackage(TestCase):
    config_file = '/path/to/mopack.yml'
    pkgdir = '/path/to/builddir/mopack'
    deploy_paths = {'prefix': '/usr/local'}

    def test_basic(self):
        pkg = SystemPackage('foo', config_file=self.config_file)

        info = SystemPackage.resolve_all(self.pkgdir, [pkg], self.deploy_paths)
        self.assertEqual(info, [
            {'config': {'source': 'system', 'name': 'foo',
                        'config_file': self.config_file},
             'usage': {'type': 'system'}},
        ])

    def test_multiple(self):
        pkg1 = SystemPackage('foo', config_file=self.config_file)
        pkg2 = SystemPackage('bar', config_file=self.config_file)

        info = SystemPackage.resolve_all(self.pkgdir, [pkg1, pkg2],
                                         self.deploy_paths)
        self.assertEqual(info, [
            {'config': {'source': 'system', 'name': 'foo',
                        'config_file': self.config_file},
             'usage': {'type': 'system'}},
            {'config': {'source': 'system', 'name': 'bar',
                        'config_file': self.config_file},
             'usage': {'type': 'system'}},
        ])

    def test_deploy(self):
        pkg = SystemPackage('foo', config_file=self.config_file)
        # This is a no-op; just make sure it executes ok.
        AptPackage.deploy_all(self.pkgdir, [pkg])

    def test_clean_pre(self):
        oldpkg = SystemPackage('foo', config_file=self.config_file)
        newpkg = AptPackage('foo', config_file=self.config_file)

        # System -> Apt
        self.assertEqual(oldpkg.clean_pre(self.pkgdir, newpkg), False)

        # Apt -> nothing
        self.assertEqual(oldpkg.clean_pre(self.pkgdir, None), False)

    def test_clean_post(self):
        oldpkg = SystemPackage('foo', config_file=self.config_file)
        newpkg = AptPackage('foo', config_file=self.config_file)

        # System -> Apt
        self.assertEqual(oldpkg.clean_post(self.pkgdir, newpkg), False)

        # Apt -> nothing
        self.assertEqual(oldpkg.clean_post(self.pkgdir, None), False)

    def test_clean_all(self):
        oldpkg = SystemPackage('foo', config_file=self.config_file)
        newpkg = AptPackage('foo', config_file=self.config_file)

        # System -> Apt
        self.assertEqual(oldpkg.clean_all(self.pkgdir, newpkg), (False, False))

        # Apt -> nothing
        self.assertEqual(oldpkg.clean_all(self.pkgdir, None), (False, False))

    def test_equality(self):
        pkg = SystemPackage('foo', config_file=self.config_file)

        self.assertEqual(pkg, SystemPackage(
            'foo', config_file=self.config_file
        ))
        self.assertEqual(pkg, SystemPackage(
            'foo', config_file='/path/to/mopack2.yml'
        ))

        self.assertNotEqual(pkg, SystemPackage(
            'bar', config_file=self.config_file
        ))

    def test_rehydrate(self):
        pkg = SystemPackage('foo', config_file=self.config_file)
        data = pkg.dehydrate()
        self.assertEqual(pkg, Package.rehydrate(data))
