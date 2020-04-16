import os
from io import StringIO
from textwrap import dedent
from unittest import mock, TestCase

from .. import mock_open_log

from mopack.sources import Package
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


class TestConan(TestCase):
    config_file = '/path/to/mopack.yml'
    pkgdir = '/path/to/builddir/mopack'
    pkgconfdir = os.path.join(pkgdir, 'conan')
    deploy_paths = {'prefix': '/usr/local'}

    def test_basic(self):
        pkg = ConanPackage('foo', remote='foo/1.2.3@conan/stable',
                           config_file=self.config_file)
        self.assertEqual(pkg.remote, 'foo/1.2.3@conan/stable')
        self.assertEqual(pkg.options, {})

        with mock_open_log(mock_open_write()) as mopen, \
             mock.patch('subprocess.check_call') as mcall:  # noqa
            info = ConanPackage.resolve_all(self.pkgdir, [pkg],
                                            self.deploy_paths)
            self.assertEqual(info, [
                {'config': {'name': 'foo',
                            'config_file': self.config_file,
                            'source': 'conan',
                            'remote': 'foo/1.2.3@conan/stable',
                            'options': {},
                            'usage': {'type': 'pkgconfig', 'path': '.'}},
                 'usage': {'type': 'pkgconfig', 'path': self.pkgconfdir}},
            ])

            self.assertEqual(mopen.mock_file.getvalue(), dedent("""\
                [requires]
                foo/1.2.3@conan/stable

                [options]
            """))
            mcall.assert_called_with([
                'conan', 'install', '-g', 'pkg_config', '-if',
                os.path.join(self.pkgdir, 'conan'), self.pkgdir
            ], stdout=mopen(), stderr=mopen())

    def test_options(self):
        pkg = ConanPackage('foo', remote='foo/1.2.3@conan/stable',
                           options={'shared': True},
                           config_file=self.config_file)
        self.assertEqual(pkg.remote, 'foo/1.2.3@conan/stable')
        self.assertEqual(pkg.options, {'shared': True})

        with mock_open_log(mock_open_write()) as mopen, \
             mock.patch('subprocess.check_call') as mcall:  # noqa
            info = ConanPackage.resolve_all(self.pkgdir, [pkg],
                                            self.deploy_paths)
            self.assertEqual(info, [
                {'config': {'name': 'foo',
                            'config_file': self.config_file,
                            'source': 'conan',
                            'remote': 'foo/1.2.3@conan/stable',
                            'options': {'shared': True},
                            'usage': {'type': 'pkgconfig', 'path': '.'}},
                 'usage': {'type': 'pkgconfig', 'path': self.pkgconfdir}},
            ])

            self.assertEqual(mopen.mock_file.getvalue(), dedent("""\
                [requires]
                foo/1.2.3@conan/stable

                [options]
                foo:shared=True
            """))
            mcall.assert_called_with([
                'conan', 'install', '-g', 'pkg_config', '-if',
                os.path.join(self.pkgdir, 'conan'), self.pkgdir
            ], stdout=mopen(), stderr=mopen())

    def test_multiple(self):
        pkg1 = ConanPackage('foo', remote='foo/1.2.3@conan/stable',
                            config_file=self.config_file)
        pkg2 = ConanPackage('bar', remote='bar/2.3.4@conan/stable',
                            options={'shared': True},
                            config_file=self.config_file)

        with mock_open_log(mock_open_write()) as mopen, \
             mock.patch('subprocess.check_call') as mcall:  # noqa
            info = ConanPackage.resolve_all(self.pkgdir, [pkg1, pkg2],
                                            self.deploy_paths)
            self.assertEqual(info, [
                {'config': {'name': 'foo',
                            'config_file': self.config_file,
                            'source': 'conan',
                            'remote': 'foo/1.2.3@conan/stable',
                            'options': {},
                            'usage': {'type': 'pkgconfig', 'path': '.'}},
                 'usage': {'type': 'pkgconfig', 'path': self.pkgconfdir}},
                {'config': {'name': 'bar',
                            'config_file': self.config_file,
                            'source': 'conan',
                            'remote': 'bar/2.3.4@conan/stable',
                            'options': {'shared': True},
                            'usage': {'type': 'pkgconfig', 'path': '.'}},
                 'usage': {'type': 'pkgconfig', 'path': self.pkgconfdir}},
            ])

            self.assertEqual(mopen.mock_file.getvalue(), dedent("""\
                [requires]
                foo/1.2.3@conan/stable
                bar/2.3.4@conan/stable

                [options]
                bar:shared=True
            """))
            mcall.assert_called_with([
                'conan', 'install', '-g', 'pkg_config', '-if',
                os.path.join(self.pkgdir, 'conan'), self.pkgdir
            ], stdout=mopen(), stderr=mopen())

    def test_deploy(self):
        pkg = ConanPackage('foo', remote='foo/1.2.3@conan/stable',
                           config_file=self.config_file)
        with mock.patch('warnings.warn') as mwarn:
            ConanPackage.deploy_all(self.pkgdir, [pkg])
            mwarn.assert_called_once()

    def test_clean(self):
        oldpkg = ConanPackage('foo', remote='foo/1.2.3@conan/stable',
                              config_file=self.config_file)
        newpkg1 = ConanPackage('foo', remote='foo/1.2.4@conan/stable',
                               config_file=self.config_file)
        newpkg2 = AptPackage('foo', config_file=self.config_file)

        # Conan -> Conan
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch('os.remove') as mremove:  # noqa
            self.assertEqual(oldpkg.clean_needed(self.pkgdir, newpkg1), False)
            mlog.assert_not_called()
            mremove.assert_not_called()

        # Conan -> Apt
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch('os.remove') as mremove:  # noqa
            self.assertEqual(oldpkg.clean_needed(self.pkgdir, newpkg2), True)
            mlog.assert_called_once()
            mremove.assert_called_once_with(os.path.join(
                self.pkgdir, 'conan', 'foo.pc'
            ))

        # Conan -> nothing
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch('os.remove') as mremove:  # noqa
            self.assertEqual(oldpkg.clean_needed(self.pkgdir, None), True)
            mlog.assert_called_once()
            mremove.assert_called_once_with(os.path.join(
                self.pkgdir, 'conan', 'foo.pc'
            ))

        # Error deleting
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch('os.remove',
                        side_effect=FileNotFoundError) as mremove:  # noqa
            self.assertEqual(oldpkg.clean_needed(self.pkgdir, None), True)
            mlog.assert_called_once()
            mremove.assert_called_once_with(os.path.join(
                self.pkgdir, 'conan', 'foo.pc'
            ))

    def test_equality(self):
        remote = 'foo/1.2.3@conan/stable'
        options = {'shared': True}
        pkg = ConanPackage('foo', remote=remote, options=options,
                           config_file=self.config_file)

        self.assertEqual(pkg, ConanPackage(
            'foo', remote=remote, options=options, config_file=self.config_file
        ))
        self.assertEqual(pkg, ConanPackage(
            'foo', remote=remote, options=options,
            config_file='/path/to/mopack2.yml'
        ))

        self.assertNotEqual(pkg, ConanPackage(
            'bar', remote=remote, options=options, config_file=self.config_file
        ))
        self.assertNotEqual(pkg, ConanPackage(
            'foo', remote='foo/1.2.4@conan/stable', options=options,
            config_file=self.config_file
        ))
        self.assertNotEqual(pkg, ConanPackage(
            'foo', remote=remote, config_file=self.config_file
        ))

    def test_rehydrate(self):
        pkg = ConanPackage('foo', remote='foo/1.2.3@conan/stable',
                           options={'shared': True},
                           config_file=self.config_file)
        data = pkg.dehydrate()
        self.assertEqual(pkg, Package.rehydrate(data))
