import os
from unittest import mock, TestCase

from .. import mock_open_log

from mopack.sources import Package
from mopack.sources.apt import AptPackage
from mopack.sources.conan import ConanPackage


class TestApt(TestCase):
    pkgdir = '/path/to/builddir/mopack'
    deploy_paths = {'prefix': '/usr/local'}

    def test_basic(self):
        pkg = AptPackage('foo', config_file='/path/to/mopack.yml')
        self.assertEqual(pkg.remote, 'libfoo-dev')

        with mock_open_log() as mopen, \
             mock.patch('subprocess.check_call') as mcall:  # noqa
            AptPackage.resolve_all(self.pkgdir, [pkg], self.deploy_paths)
            mopen.assert_called_with(os.path.join(self.pkgdir, 'apt.log'), 'w')
            mcall.assert_called_with([
                'sudo', 'apt-get', 'install', '-y', 'libfoo-dev'
            ], stdout=mopen(), stderr=mopen())

    def test_remote(self):
        pkg = AptPackage('foo', remote='foo-dev',
                         config_file='/path/to/mopack.yml')
        self.assertEqual(pkg.remote, 'foo-dev')

        with mock_open_log() as mopen, \
             mock.patch('subprocess.check_call') as mcall:  # noqa
            AptPackage.resolve_all(self.pkgdir, [pkg], self.deploy_paths)
            mopen.assert_called_with(os.path.join(self.pkgdir, 'apt.log'), 'w')
            mcall.assert_called_with([
                'sudo', 'apt-get', 'install', '-y', 'foo-dev'
            ], stdout=mopen(), stderr=mopen())

    def test_multiple(self):
        pkg1 = AptPackage('foo', config_file='/path/to/mopack.yml')
        pkg2 = AptPackage('bar', remote='bar-dev',
                          config_file='/path/to/mopack.yml')

        with mock_open_log() as mopen, \
             mock.patch('subprocess.check_call') as mcall:  # noqa
            AptPackage.resolve_all(self.pkgdir, [pkg1, pkg2],
                                   self.deploy_paths)
            mopen.assert_called_with(os.path.join(self.pkgdir, 'apt.log'), 'w')
            mcall.assert_called_with([
                'sudo', 'apt-get', 'install', '-y', 'libfoo-dev', 'bar-dev'
            ], stdout=mopen(), stderr=mopen())

    def test_deploy(self):
        pkg = AptPackage('foo', config_file='/path/to/mopack.yml')
        # This is a no-op; just make sure it executes ok.
        AptPackage.deploy_all(self.pkgdir, [pkg])

    def test_clean(self):
        oldpkg = AptPackage('foo', config_file='/path/to/mopack.yml')
        newpkg = ConanPackage('foo', remote='foo/1.2.4@conan/stable',
                              config_file='/path/to/mopack.yml')

        # Apt -> Conan
        self.assertEqual(oldpkg.clean_needed(self.pkgdir, newpkg), False)

        # Apt -> nothing
        self.assertEqual(oldpkg.clean_needed(self.pkgdir, None), False)

    def test_equality(self):
        config_file = '/path/to/mopack.yml'
        pkg = AptPackage('foo', config_file=config_file)

        self.assertEqual(pkg, AptPackage('foo', config_file=config_file))
        self.assertEqual(pkg, AptPackage('foo', remote='libfoo-dev',
                                         config_file=config_file))
        self.assertEqual(pkg, AptPackage('foo',
                                         config_file='/path/to/mopack2.yml'))

        self.assertNotEqual(pkg, AptPackage('bar', config_file=config_file))
        self.assertNotEqual(pkg, AptPackage('bar', remote='libfoo-dev',
                                            config_file=config_file))
        self.assertNotEqual(pkg, AptPackage('foo', remote='libbar-dev',
                                            config_file=config_file))

    def test_rehydrate(self):
        pkg = AptPackage('foo', remote='libbar-dev',
                         config_file='/path/to/mopack.yml')
        data = pkg.dehydrate()
        self.assertEqual(pkg, Package.rehydrate(data))