import os
import subprocess
from unittest import mock

from . import *
from .... import *

from mopack.builders.bfg9000 import Bfg9000Builder
from mopack.config import Config
from mopack.sources import Package
from mopack.sources.apt import AptPackage
from mopack.sources.sdist import TarballPackage


class TestTarball(SDistTestCase):
    pkg_type = TarballPackage
    srcurl = 'http://example.invalid/hello-bfg.tar.gz'
    srcpath = os.path.join(test_data_dir, 'hello-bfg.tar.gz')

    def mock_urlopen(self, url):
        return open(self.srcpath, 'rb')

    def check_fetch(self, pkg):
        srcdir = os.path.join(self.pkgdir, 'src', 'foo')
        with mock.patch('mopack.sources.sdist.urlopen', self.mock_urlopen), \
             mock.patch('tarfile.TarFile.extractall') as mtar:  # noqa
            pkg.fetch(self.pkgdir, None)
            mtar.assert_called_once_with(srcdir, None)

    def test_url(self):
        pkg = self.make_package('foo', url=self.srcurl, build='bfg9000')
        self.assertEqual(pkg.url, self.srcurl)
        self.assertEqual(pkg.path, None)
        self.assertEqual(pkg.patch, None)
        self.assertEqual(pkg.builder, self.make_builder(Bfg9000Builder, 'foo'))
        self.assertEqual(pkg.should_deploy, True)

        self.check_fetch(pkg)
        self.check_resolve(pkg)

    def test_path(self):
        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000')
        self.assertEqual(pkg.url, None)
        self.assertEqual(pkg.path, self.srcpath)
        self.assertEqual(pkg.patch, None)
        self.assertEqual(pkg.builder, self.make_builder(Bfg9000Builder, 'foo'))
        self.assertEqual(pkg.should_deploy, True)

        self.check_fetch(pkg)
        self.check_resolve(pkg)

    def test_zip_path(self):
        srcpath = os.path.join(test_data_dir, 'hello-bfg.zip')
        pkg = self.make_package('foo', build='bfg9000', path=srcpath)
        self.assertEqual(pkg.url, None)
        self.assertEqual(pkg.path, srcpath)
        self.assertEqual(pkg.builder, self.make_builder(Bfg9000Builder, 'foo'))
        self.assertEqual(pkg.should_deploy, True)

        srcdir = os.path.join(self.pkgdir, 'src', 'foo')
        with mock.patch('mopack.sources.sdist.urlopen', self.mock_urlopen), \
             mock.patch('zipfile.ZipFile.extractall') as mtar:  # noqa
            pkg.fetch(self.pkgdir, None)
            mtar.assert_called_once_with(srcdir, None)
        self.check_resolve(pkg)

    def test_invalid_url_path(self):
        with self.assertRaises(TypeError):
            self.make_package('foo', build='bfg9000')
        with self.assertRaises(TypeError):
            self.make_package('foo', url=self.srcurl, path=self.srcpath,
                              build='bfg9000')

    def test_files(self):
        pkg = self.make_package('foo', path=self.srcpath,
                                files='/hello-bfg/include/', build='bfg9000')
        self.assertEqual(pkg.files, ['/hello-bfg/include/'])

        srcdir = os.path.join(self.pkgdir, 'src', 'foo')
        with mock.patch('mopack.sources.sdist.urlopen', self.mock_urlopen), \
             mock.patch('tarfile.TarFile.extract') as mtar:  # noqa
            pkg.fetch(self.pkgdir, None)
            self.assertEqual(mtar.mock_calls, [
                mock.call('hello-bfg/include', srcdir),
                mock.call('hello-bfg/include/hello.hpp', srcdir),
            ])
        self.check_resolve(pkg)

    def test_patch(self):
        patch = os.path.join(test_data_dir, 'hello-bfg.patch')
        pkg = self.make_package('foo', path=self.srcpath, patch=patch,
                                build='bfg9000')
        self.assertEqual(pkg.patch, patch)

        srcdir = os.path.join(self.pkgdir, 'src', 'foo')
        with mock.patch('mopack.sources.sdist.urlopen', self.mock_urlopen), \
             mock.patch('mopack.sources.sdist.pushd'), \
             mock.patch('tarfile.TarFile.extractall') as mtar, \
             mock.patch('builtins.open', mock_open_after_first()) as mopen, \
             mock.patch('os.makedirs'), \
             mock.patch('subprocess.run') as mrun:  # noqa
            pkg.fetch(self.pkgdir, None)
            mtar.assert_called_once_with(srcdir, None)
            mrun.assert_called_once_with(
                ['patch', '-p1'], stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, stdin=mopen(),
                universal_newlines=True, check=True
            )
        self.check_resolve(pkg)

    def test_build(self):
        build = {'type': 'bfg9000', 'extra_args': '--extra'}
        pkg = self.make_package('foo', path=self.srcpath, build=build,
                                usage='pkg-config')
        self.assertEqual(pkg.path, self.srcpath)
        self.assertEqual(pkg.builder, self.make_builder(
            Bfg9000Builder, 'foo', extra_args='--extra'
        ))

        self.check_fetch(pkg)
        self.check_resolve(pkg)

    def test_infer_build(self):
        def mock_exists(p):
            return os.path.basename(p) == 'mopack.yml'

        pkg = self.make_package('foo', path=self.srcpath, set_options=False)
        self.assertEqual(pkg.builder, None)

        with mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock_open_after_first(
                 read_data='self:\n  build: bfg9000'
             )), \
             mock.patch('tarfile.TarFile.extractall') as mtar:  # noqa
            config = pkg.fetch(self.pkgdir, Config([]))
            self.set_options(pkg)
            self.assertEqual(config.build, 'bfg9000')
            self.assertEqual(pkg.builder, self.make_builder(
                Bfg9000Builder, 'foo'
            ))
        self.check_resolve(pkg)

        pkg = self.make_package('foo', path=self.srcpath,
                                usage={'type': 'system'}, set_options=False)

        with mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock_open_after_first(
                 read_data='self:\n  build: bfg9000'
             )), \
             mock.patch('tarfile.TarFile.extractall') as mtar:  # noqa
            config = pkg.fetch(self.pkgdir, Config([]))
            self.set_options(pkg)
            self.assertEqual(config.build, 'bfg9000')
            self.assertEqual(pkg.builder, self.make_builder(
                Bfg9000Builder, 'foo', usage={'type': 'system'}
            ))
        self.check_resolve(pkg, usage={
            'type': 'system', 'auto_link': False, 'include_path': [],
            'library_path': [], 'headers': [], 'libraries': ['foo'],
            'compile_flags': [], 'link_flags': [],
        })

    def test_usage(self):
        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                usage='pkg-config')
        self.assertEqual(pkg.path, self.srcpath)
        self.assertEqual(pkg.builder, self.make_builder(
            Bfg9000Builder, 'foo', usage='pkg-config'
        ))

        self.check_fetch(pkg)
        self.check_resolve(pkg)

        usage = {'type': 'pkg-config', 'path': 'pkgconf'}
        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                usage=usage)
        self.assertEqual(pkg.path, self.srcpath)
        self.assertEqual(pkg.builder, self.make_builder(
            Bfg9000Builder, 'foo', usage=usage
        ))

        self.check_fetch(pkg)
        self.check_resolve(pkg, usage={
            'type': 'pkg-config', 'path': self.pkgconfdir('foo', 'pkgconf'),
            'pcfiles': ['foo'], 'extra_args': [],
        })

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                submodules=submodules_required)
        self.check_fetch(pkg)
        self.check_resolve(pkg, submodules=['sub'])

        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                usage={'type': 'pkg-config', 'pcfile': 'bar'},
                                submodules=submodules_required)
        self.check_fetch(pkg)
        self.check_resolve(pkg, submodules=['sub'], usage={
            'type': 'pkg-config', 'path': self.pkgconfdir('foo'),
            'pcfiles': ['bar', 'foo_sub'], 'extra_args': [],
        })

        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                submodules=submodules_optional)
        self.check_fetch(pkg)
        self.check_resolve(pkg, submodules=['sub'])

        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                usage={'type': 'pkg-config', 'pcfile': 'bar'},
                                submodules=submodules_optional)
        self.check_fetch(pkg)
        self.check_resolve(pkg, submodules=['sub'], usage={
            'type': 'pkg-config', 'path': self.pkgconfdir('foo'),
            'pcfiles': ['bar', 'foo_sub'], 'extra_args': [],
        })

    def test_invalid_submodule(self):
        pkg = self.make_package(
            'foo', path=self.srcpath, build='bfg9000',
            submodules={'names': ['sub'], 'required': True}
        )
        with self.assertRaises(ValueError):
            pkg.get_usage(self.pkgdir, ['invalid'])

    def test_already_fetched(self):
        def mock_exists(p):
            return os.path.basename(p) == 'foo'

        build = {'type': 'bfg9000', 'extra_args': '--extra'}
        pkg = self.make_package('foo', path=self.srcpath, srcdir='srcdir',
                                build=build, usage='pkg-config')
        with mock.patch('os.path.exists', mock_exists), \
             mock.patch('tarfile.TarFile.extractall') as mtar:  # noqa
            pkg.fetch(self.pkgdir, None)
            mtar.assert_not_called()
        self.check_resolve(pkg)

    def test_deploy(self):
        pkg = self.make_package('foo', url='http://example.com',
                                build='bfg9000')
        self.assertEqual(pkg.should_deploy, True)

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('subprocess.run'):  # noqa
            pkg.deploy(self.pkgdir)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'deploy', 'foo.log'
            ), 'a')

        pkg = self.make_package('foo', url='http://example.com',
                                build='bfg9000', deploy=False)
        self.assertEqual(pkg.should_deploy, False)

        with mock_open_log() as mopen:
            pkg.deploy(self.pkgdir)
            mopen.assert_not_called()

    def test_clean_pre(self):
        otherpath = os.path.join(test_data_dir, 'other_project.tar.gz')

        oldpkg = self.make_package('foo', path=self.srcpath,
                                   srcdir='bfg_project', build='bfg9000')
        newpkg1 = self.make_package('foo', path=otherpath, build='bfg9000')
        newpkg2 = self.make_package(AptPackage, 'foo')

        srcdir = os.path.join(self.pkgdir, 'src', 'foo')

        # Tarball -> Tarball (same)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch('shutil.rmtree') as mrmtree:  # noqa
            self.assertEqual(oldpkg.clean_pre(self.pkgdir, oldpkg), False)
            mlog.assert_not_called()
            mrmtree.assert_not_called()

        # Tarball -> Tarball (different)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch('shutil.rmtree') as mrmtree:  # noqa
            self.assertEqual(oldpkg.clean_pre(self.pkgdir, newpkg1), True)
            mlog.assert_called_once()
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

        # Tarball -> Apt
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch('shutil.rmtree') as mrmtree:  # noqa
            self.assertEqual(oldpkg.clean_pre(self.pkgdir, newpkg2), True)
            mlog.assert_called_once()
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

        # Tarball -> nothing
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch('shutil.rmtree') as mrmtree:  # noqa
            self.assertEqual(oldpkg.clean_pre(self.pkgdir, None), True)
            mlog.assert_called_once()
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

    def test_clean_post(self):
        otherpath = os.path.join(test_data_dir, 'other_project.tar.gz')

        oldpkg = self.make_package('foo', path=self.srcpath,
                                   srcdir='bfg_project', build='bfg9000')
        newpkg1 = self.make_package('foo', path=otherpath, build='bfg9000')
        newpkg2 = self.make_package(AptPackage, 'foo')

        # Tarball -> Tarball (same)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, oldpkg), False)
            mlog.assert_not_called()
            mclean.assert_not_called()

        # Tarball -> Tarball (different)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, newpkg1), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)

        # Tarball -> Apt
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, newpkg2), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)

        # Tarball -> nothing
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, None), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)

    def test_clean_all(self):
        otherpath = os.path.join(test_data_dir, 'other_project.tar.gz')

        oldpkg = self.make_package('foo', path=self.srcpath,
                                   srcdir='bfg_project', build='bfg9000')
        newpkg1 = self.make_package('foo', path=otherpath, build='bfg9000')
        newpkg2 = self.make_package(AptPackage, 'foo')

        srcdir = os.path.join(self.pkgdir, 'src', 'foo')

        # Tarball -> Tarball (same)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean, \
             mock.patch('shutil.rmtree') as mrmtree:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, oldpkg),
                             (False, False))
            mlog.assert_not_called()
            mclean.assert_not_called()
            mrmtree.assert_not_called()

        # Tarball -> Tarball (different)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean, \
             mock.patch('shutil.rmtree') as mrmtree:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, newpkg1),
                             (True, True))
            self.assertEqual(mlog.call_count, 2)
            mclean.assert_called_once_with(self.pkgdir)
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

        # Tarball -> Apt
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean, \
             mock.patch('shutil.rmtree') as mrmtree:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, newpkg2),
                             (True, True))
            self.assertEqual(mlog.call_count, 2)
            mclean.assert_called_once_with(self.pkgdir)
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

        # Tarball -> nothing
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean, \
             mock.patch('shutil.rmtree') as mrmtree:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, None),
                             (True, True))
            self.assertEqual(mlog.call_count, 2)
            mclean.assert_called_once_with(self.pkgdir)
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

    def test_equality(self):
        otherpath = os.path.join(test_data_dir, 'other_project.tar.gz')
        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000')

        self.assertEqual(pkg, self.make_package(
            'foo', path=self.srcpath, build='bfg9000'
        ))
        self.assertEqual(pkg, self.make_package(
            'foo', path=self.srcpath, build='bfg9000',
            config_file='/path/to/mopack2.yml'
        ))

        self.assertNotEqual(pkg, self.make_package(
            'bar', path=self.srcpath, build='bfg9000'
        ))
        self.assertNotEqual(pkg, self.make_package(
            'foo', url=self.srcurl, build='bfg9000'
        ))
        self.assertNotEqual(pkg, self.make_package(
            'foo', path=otherpath, build='bfg9000'
        ))

    def test_rehydrate(self):
        pkg = TarballPackage('foo', path=self.srcpath, build='bfg9000',
                             config_file=self.config_file)
        data = pkg.dehydrate()
        self.assertEqual(pkg, Package.rehydrate(data))

        pkg = TarballPackage('foo', path=self.srcpath,
                             config_file=self.config_file)
        with self.assertRaises(TypeError):
            data = pkg.dehydrate()

    def test_builder_types(self):
        pkg = TarballPackage('foo', path=self.srcpath, build='bfg9000',
                             config_file=self.config_file)
        self.assertEqual(pkg.builder_types, ['bfg9000'])

        pkg = TarballPackage('foo', path=self.srcpath,
                             config_file=self.config_file)
        with self.assertRaises(TypeError):
            pkg.builder_types
