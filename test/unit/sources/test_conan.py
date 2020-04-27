import os
from io import StringIO
from textwrap import dedent
from unittest import mock

from . import SourceTest
from .. import mock_open_log

from mopack.sources import Package, ResolvedPackage
from mopack.sources.apt import AptPackage
from mopack.sources.conan import ConanPackage


def mock_open_write():
    class MockFile(StringIO):
        def close(self):
            pass

    mock_open = mock.mock_open()

    def non_mock(*args, **kwargs):
        mock_open.side_effect = None
        mock_open.mock_file = MockFile()
        return mock_open.mock_file

    mock_open.side_effect = non_mock
    return mock_open


class TestConan(SourceTest):
    pkg_type = ConanPackage
    config_file = '/path/to/mopack.yml'
    pkgdir = '/path/to/builddir/mopack'
    pkgconfdir = os.path.join(pkgdir, 'conan')
    deploy_paths = {'prefix': '/usr/local'}

    def test_basic(self):
        pkg = self.make_package('foo', remote='foo/1.2.3@conan/stable')
        self.assertEqual(pkg.remote, 'foo/1.2.3@conan/stable')
        self.assertEqual(pkg.options, {})

        with mock_open_log(mock_open_write()) as mopen, \
             mock.patch('subprocess.check_call') as mcall:  # noqa
            info = ConanPackage.resolve_all(self.pkgdir, [pkg],
                                            self.deploy_paths)
            self.assertEqual(info, [
                ResolvedPackage(pkg, {'type': 'pkg-config',
                                      'path': self.pkgconfdir}),
            ])

            self.assertEqual(mopen.mock_file.getvalue(), dedent("""\
                [requires]
                foo/1.2.3@conan/stable

                [options]

                [generators]
                pkg_config
            """))
            mcall.assert_called_with([
                'conan', 'install', '-if', os.path.join(self.pkgdir, 'conan'),
                self.pkgdir
            ], stdout=mopen(), stderr=mopen())

    def test_options(self):
        pkg = self.make_package('foo', remote='foo/1.2.3@conan/stable',
                                options={'shared': True})
        self.assertEqual(pkg.remote, 'foo/1.2.3@conan/stable')
        self.assertEqual(pkg.options, {'shared': True})

        with mock_open_log(mock_open_write()) as mopen, \
             mock.patch('subprocess.check_call') as mcall:  # noqa
            info = ConanPackage.resolve_all(self.pkgdir, [pkg],
                                            self.deploy_paths)
            self.assertEqual(info, [
                ResolvedPackage(pkg, {'type': 'pkg-config',
                                      'path': self.pkgconfdir}),
            ])

            self.assertEqual(mopen.mock_file.getvalue(), dedent("""\
                [requires]
                foo/1.2.3@conan/stable

                [options]
                foo:shared=True

                [generators]
                pkg_config
            """))
            mcall.assert_called_with([
                'conan', 'install', '-if', os.path.join(self.pkgdir, 'conan'),
                self.pkgdir
            ], stdout=mopen(), stderr=mopen())

    def test_global_options(self):
        pkg = self.make_package('foo', remote='foo/1.2.3@conan/stable',
                                global_options={'generator': 'cmake'})
        self.assertEqual(pkg.remote, 'foo/1.2.3@conan/stable')
        self.assertEqual(pkg.options, {})

        with mock_open_log(mock_open_write()) as mopen, \
             mock.patch('subprocess.check_call') as mcall:  # noqa
            info = ConanPackage.resolve_all(self.pkgdir, [pkg],
                                            self.deploy_paths)
            self.assertEqual(info, [
                ResolvedPackage(pkg, {'type': 'pkg-config',
                                      'path': self.pkgconfdir}),
            ])

            self.assertEqual(mopen.mock_file.getvalue(), dedent("""\
                [requires]
                foo/1.2.3@conan/stable

                [options]

                [generators]
                pkg_config
                cmake
            """))
            mcall.assert_called_with([
                'conan', 'install', '-if', os.path.join(self.pkgdir, 'conan'),
                self.pkgdir
            ], stdout=mopen(), stderr=mopen())

    def test_multiple(self):
        pkg1 = self.make_package('foo', remote='foo/1.2.3@conan/stable')
        pkg2 = self.make_package('bar', remote='bar/2.3.4@conan/stable',
                                 options={'shared': True})

        with mock_open_log(mock_open_write()) as mopen, \
             mock.patch('subprocess.check_call') as mcall:  # noqa
            info = ConanPackage.resolve_all(self.pkgdir, [pkg1, pkg2],
                                            self.deploy_paths)
            self.assertEqual(info, [
                ResolvedPackage(pkg1, {'type': 'pkg-config',
                                       'path': self.pkgconfdir}),
                ResolvedPackage(pkg2, {'type': 'pkg-config',
                                       'path': self.pkgconfdir}),
            ])

            self.assertEqual(mopen.mock_file.getvalue(), dedent("""\
                [requires]
                foo/1.2.3@conan/stable
                bar/2.3.4@conan/stable

                [options]
                bar:shared=True

                [generators]
                pkg_config
            """))
            mcall.assert_called_with([
                'conan', 'install', '-if', os.path.join(self.pkgdir, 'conan'),
                self.pkgdir
            ], stdout=mopen(), stderr=mopen())

    def test_deploy(self):
        pkg = self.make_package('foo', remote='foo/1.2.3@conan/stable')
        with mock.patch('warnings.warn') as mwarn:
            ConanPackage.deploy_all(self.pkgdir, [pkg])
            mwarn.assert_called_once()

    def test_clean_pre(self):
        oldpkg = self.make_package('foo', remote='foo/1.2.3@conan/stable')
        newpkg = self.make_package(AptPackage, 'foo')

        # Conan -> Apt
        self.assertEqual(oldpkg.clean_pre(self.pkgdir, newpkg), False)

        # Conan -> Nothing
        self.assertEqual(oldpkg.clean_pre(self.pkgdir, None), False)

    def test_clean_post(self):
        oldpkg = self.make_package('foo', remote='foo/1.2.3@conan/stable')
        newpkg1 = self.make_package('foo', remote='foo/1.2.4@conan/stable')
        newpkg2 = self.make_package(AptPackage, 'foo')

        # Conan -> Conan
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch('os.remove') as mremove:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, newpkg1), False)
            mlog.assert_not_called()
            mremove.assert_not_called()

        # Conan -> Apt
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch('os.remove') as mremove:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, newpkg2), True)
            mlog.assert_called_once()
            mremove.assert_called_once_with(os.path.join(
                self.pkgdir, 'conan', 'foo.pc'
            ))

        # Conan -> nothing
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch('os.remove') as mremove:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, None), True)
            mlog.assert_called_once()
            mremove.assert_called_once_with(os.path.join(
                self.pkgdir, 'conan', 'foo.pc'
            ))

        # Error deleting
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch('os.remove',
                        side_effect=FileNotFoundError) as mremove:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, None), True)
            mlog.assert_called_once()
            mremove.assert_called_once_with(os.path.join(
                self.pkgdir, 'conan', 'foo.pc'
            ))

    def test_clean_all(self):
        oldpkg = self.make_package('foo', remote='foo/1.2.3@conan/stable')
        newpkg1 = self.make_package('foo', remote='foo/1.2.4@conan/stable')
        newpkg2 = self.make_package(AptPackage, 'foo')

        # Conan -> Conan
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch('os.remove') as mremove:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, newpkg1),
                             (False, False))
            mlog.assert_not_called()
            mremove.assert_not_called()

        # Conan -> Apt
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch('os.remove') as mremove:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, newpkg2),
                             (False, True))
            mlog.assert_called_once()
            mremove.assert_called_once_with(os.path.join(
                self.pkgdir, 'conan', 'foo.pc'
            ))

        # Conan -> nothing
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch('os.remove') as mremove:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, None),
                             (False, True))
            mlog.assert_called_once()
            mremove.assert_called_once_with(os.path.join(
                self.pkgdir, 'conan', 'foo.pc'
            ))

        # Error deleting
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch('os.remove',
                        side_effect=FileNotFoundError) as mremove:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, None),
                             (False, True))
            mlog.assert_called_once()
            mremove.assert_called_once_with(os.path.join(
                self.pkgdir, 'conan', 'foo.pc'
            ))

    def test_equality(self):
        remote = 'foo/1.2.3@conan/stable'
        options = {'shared': True}
        pkg = self.make_package('foo', remote=remote, options=options)

        self.assertEqual(pkg, self.make_package(
            'foo', remote=remote, options=options
        ))
        self.assertEqual(pkg, self.make_package(
            'foo', remote=remote, options=options,
            config_file='/path/to/mopack2.yml'
        ))

        self.assertNotEqual(pkg, self.make_package(
            'bar', remote=remote, options=options
        ))
        self.assertNotEqual(pkg, self.make_package(
            'foo', remote='foo/1.2.4@conan/stable', options=options
        ))
        self.assertNotEqual(pkg, self.make_package('foo', remote=remote))

    def test_rehydrate(self):
        pkg = ConanPackage('foo', remote='foo/1.2.3@conan/stable',
                           options={'shared': True},
                           config_file=self.config_file)
        data = pkg.dehydrate()
        self.assertEqual(pkg, Package.rehydrate(data))
