import os
import subprocess
from io import StringIO
from textwrap import dedent
from unittest import mock, TestCase

from . import SourceTest
from .. import mock_open_log

from mopack.iterutils import iterate
from mopack.sources import Package, PackageOptions
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
    config_file = os.path.abspath('/path/to/mopack.yml')
    pkgdir = os.path.abspath('/path/to/builddir/mopack')
    pkgconfdir = os.path.join(pkgdir, 'conan')
    deploy_paths = {'prefix': '/usr/local'}

    def check_usage(self, pkg, *, submodules=None, usage=None):
        if usage is None:
            pcfiles = ([] if pkg.submodules and pkg.submodules['required'] else
                       [pkg.name])
            pcfiles.extend('{}_{}'.format(pkg.name, i)
                           for i in iterate(submodules))
            usage = {'type': 'pkg-config', 'path': self.pkgconfdir,
                     'pcfiles': pcfiles, 'extra_args': []}
        self.assertEqual(pkg.get_usage(self.pkgdir, submodules), usage)

    def test_basic(self):
        pkg = self.make_package('foo', remote='foo/1.2.3@conan/stable')
        self.assertEqual(pkg.remote, 'foo/1.2.3@conan/stable')
        self.assertEqual(pkg.options, {})
        self.assertEqual(pkg.should_deploy, True)

        with mock_open_log(mock_open_write()) as mopen, \
             mock.patch('subprocess.run') as mcall:  # noqa
            ConanPackage.resolve_all(self.pkgdir, [pkg], self.deploy_paths)

            self.assertEqual(mopen.mock_file.getvalue(), dedent("""\
                [requires]
                foo/1.2.3@conan/stable

                [options]

                [generators]
                pkg_config
            """))
            mcall.assert_called_with(
                ['conan', 'install', '-if', os.path.join(self.pkgdir, 'conan'),
                 self.pkgdir], stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, universal_newlines=True, check=True
            )

        self.check_usage(pkg)

    def test_options(self):
        pkg = self.make_package('foo', remote='foo/1.2.3@conan/stable',
                                options={'shared': True})
        self.assertEqual(pkg.remote, 'foo/1.2.3@conan/stable')
        self.assertEqual(pkg.options, {'shared': True})
        self.assertEqual(pkg.should_deploy, True)

        with mock_open_log(mock_open_write()) as mopen, \
             mock.patch('subprocess.run') as mcall:  # noqa
            ConanPackage.resolve_all(self.pkgdir, [pkg], self.deploy_paths)

            self.assertEqual(mopen.mock_file.getvalue(), dedent("""\
                [requires]
                foo/1.2.3@conan/stable

                [options]
                foo:shared=True

                [generators]
                pkg_config
            """))
            mcall.assert_called_with(
                ['conan', 'install', '-if', os.path.join(self.pkgdir, 'conan'),
                 self.pkgdir], stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, universal_newlines=True, check=True
            )

        self.check_usage(pkg)

    def test_this_options(self):
        pkg = self.make_package('foo', remote='foo/1.2.3@conan/stable',
                                this_options={'generator': 'cmake',
                                              'build': 'foo'})
        self.assertEqual(pkg.remote, 'foo/1.2.3@conan/stable')
        self.assertEqual(pkg.options, {})
        self.assertEqual(pkg.should_deploy, True)

        with mock_open_log(mock_open_write()) as mopen, \
             mock.patch('subprocess.run') as mcall:  # noqa
            ConanPackage.resolve_all(self.pkgdir, [pkg], self.deploy_paths)

            self.assertEqual(mopen.mock_file.getvalue(), dedent("""\
                [requires]
                foo/1.2.3@conan/stable

                [options]

                [generators]
                pkg_config
                cmake
            """))
            mcall.assert_called_with(
                ['conan', 'install', '-if', os.path.join(self.pkgdir, 'conan'),
                 '--build', 'foo', self.pkgdir], stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, universal_newlines=True, check=True
            )

        self.check_usage(pkg)

    def test_this_options_build_all(self):
        pkg = self.make_package('foo', remote='foo/1.2.3@conan/stable',
                                this_options={'generator': 'cmake',
                                              'build': 'all'})
        self.assertEqual(pkg.remote, 'foo/1.2.3@conan/stable')
        self.assertEqual(pkg.options, {})
        self.assertEqual(pkg.should_deploy, True)

        with mock_open_log(mock_open_write()) as mopen, \
             mock.patch('subprocess.run') as mcall:  # noqa
            ConanPackage.resolve_all(self.pkgdir, [pkg], self.deploy_paths)

            self.assertEqual(mopen.mock_file.getvalue(), dedent("""\
                [requires]
                foo/1.2.3@conan/stable

                [options]

                [generators]
                pkg_config
                cmake
            """))
            mcall.assert_called_with(
                ['conan', 'install', '-if', os.path.join(self.pkgdir, 'conan'),
                 '--build', self.pkgdir], stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, universal_newlines=True, check=True
            )

        self.check_usage(pkg)

    def test_multiple(self):
        pkgs = [
            self.make_package('foo', remote='foo/1.2.3@conan/stable'),
            self.make_package('bar', remote='bar/2.3.4@conan/stable',
                              options={'shared': True}),
        ]

        with mock_open_log(mock_open_write()) as mopen, \
             mock.patch('subprocess.run') as mcall:  # noqa
            ConanPackage.resolve_all(self.pkgdir, pkgs, self.deploy_paths)

            self.assertEqual(mopen.mock_file.getvalue(), dedent("""\
                [requires]
                foo/1.2.3@conan/stable
                bar/2.3.4@conan/stable

                [options]
                bar:shared=True

                [generators]
                pkg_config
            """))
            mcall.assert_called_with(
                ['conan', 'install', '-if', os.path.join(self.pkgdir, 'conan'),
                 self.pkgdir], stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, universal_newlines=True, check=True
            )

        for pkg in pkgs:
            self.check_usage(pkg)

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        pkg = self.make_package('foo', remote='foo/1.2.3@conan/stable',
                                submodules=submodules_required)
        self.check_usage(pkg, submodules=['sub'])

        pkg = self.make_package('foo', remote='foo/1.2.3@conan/stable',
                                usage={'type': 'pkg-config', 'path': '.',
                                       'pcfile': 'bar'},
                                submodules=submodules_required)
        self.check_usage(pkg, submodules=['sub'], usage={
            'type': 'pkg-config', 'path': self.pkgconfdir,
            'pcfiles': ['bar', 'foo_sub'], 'extra_args': [],
        })

        pkg = self.make_package('foo', remote='foo/1.2.3@conan/stable',
                                submodules=submodules_optional)
        self.check_usage(pkg, submodules=['sub'])

        pkg = self.make_package('foo', remote='foo/1.2.3@conan/stable',
                                usage={'type': 'pkg-config', 'path': '.',
                                       'pcfile': 'bar'},
                                submodules=submodules_optional)
        self.check_usage(pkg, submodules=['sub'], usage={
            'type': 'pkg-config', 'path': self.pkgconfdir,
            'pcfiles': ['bar', 'foo_sub'], 'extra_args': [],
        })

    def test_invalid_submodule(self):
        pkg = self.make_package(
            'foo', remote='foo/1.2.3@conan/stable',
            submodules={'names': ['sub'], 'required': True}
        )
        with self.assertRaises(ValueError):
            pkg.get_usage(self.pkgdir, ['invalid'])

    def test_deploy(self):
        pkg = self.make_package('foo', remote='foo/1.2.3@conan/stable')
        self.assertEqual(pkg.should_deploy, True)
        with mock.patch('warnings.warn') as mwarn:
            ConanPackage.deploy_all(self.pkgdir, [pkg])
            mwarn.assert_called_once()

        pkg = self.make_package('foo', remote='foo/1.2.3@conan/stable',
                                deploy=False)
        self.assertEqual(pkg.should_deploy, False)
        with mock.patch('warnings.warn') as mwarn:
            ConanPackage.deploy_all(self.pkgdir, [pkg])
            mwarn.assert_not_called()

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
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch('os.remove') as mremove:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, newpkg1), False)
            mlog.assert_not_called()
            mremove.assert_not_called()

        # Conan -> Apt
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch('os.remove') as mremove:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, newpkg2), True)
            mlog.assert_called_once()
            mremove.assert_called_once_with(os.path.join(
                self.pkgdir, 'conan', 'foo.pc'
            ))

        # Conan -> nothing
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch('os.remove') as mremove:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, None), True)
            mlog.assert_called_once()
            mremove.assert_called_once_with(os.path.join(
                self.pkgdir, 'conan', 'foo.pc'
            ))

        # Conan -> nothing (quiet)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch('os.remove') as mremove:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, None, True), True)
            mlog.assert_not_called()
            mremove.assert_called_once_with(os.path.join(
                self.pkgdir, 'conan', 'foo.pc'
            ))

        # Error deleting
        with mock.patch('mopack.log.pkg_clean') as mlog, \
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
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch('os.remove') as mremove:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, newpkg1),
                             (False, False))
            mlog.assert_not_called()
            mremove.assert_not_called()

        # Conan -> Apt
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch('os.remove') as mremove:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, newpkg2),
                             (False, True))
            mlog.assert_called_once()
            mremove.assert_called_once_with(os.path.join(
                self.pkgdir, 'conan', 'foo.pc'
            ))

        # Conan -> nothing
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch('os.remove') as mremove:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, None),
                             (False, True))
            mlog.assert_called_once()
            mremove.assert_called_once_with(os.path.join(
                self.pkgdir, 'conan', 'foo.pc'
            ))

        # Error deleting
        with mock.patch('mopack.log.pkg_clean') as mlog, \
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


class TestConanOptions(TestCase):
    def test_default(self):
        opts = ConanPackage.Options()
        self.assertEqual(opts.generator, ['pkg_config'])

    def test_generator(self):
        opts = ConanPackage.Options()
        opts(generator='cmake')
        self.assertEqual(opts.generator, ['pkg_config', 'cmake'])

        opts(generator='pkg_config')
        self.assertEqual(opts.generator, ['pkg_config', 'cmake'])

    def test_rehydrate(self):
        opts = ConanPackage.Options()
        opts(generator='cmake')
        data = opts.dehydrate()
        self.assertEqual(opts, PackageOptions.rehydrate(data))
