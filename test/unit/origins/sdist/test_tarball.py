import os
import subprocess
from unittest import mock

from . import *
from ... import assert_logging
from .... import *

from mopack.builders.bfg9000 import Bfg9000Builder
from mopack.builders.none import NoneBuilder
from mopack.config import Config
from mopack.linkages.path_system import SystemLinkage
from mopack.origins import Package
from mopack.origins.apt import AptPackage
from mopack.origins.sdist import TarballPackage
from mopack.path import Path
from mopack.types import ConfigurationError


def mock_exists(p):
    return os.path.basename(p) == 'mopack.yml'


class TestTarball(SDistTestCase):
    pkg_type = TarballPackage
    srcurl = 'http://example.invalid/hello-bfg.tar.gz'
    srcpath = os.path.join(test_data_dir, 'hello-bfg.tar.gz')

    def setUp(self):
        super().setUp()
        self.config = Config([])

    def mock_urlopen(self, url):
        return open(self.srcpath, 'rb')

    def check_fetch(self, pkg):
        srcdir = os.path.join(self.pkgdir, 'src', 'foo')
        where = pkg.url or pkg.path.string()
        with mock.patch('mopack.origins.sdist.urlopen', self.mock_urlopen), \
             mock.patch('tarfile.TarFile.extractall') as mtar, \
             mock.patch('os.path.isdir', return_value=True), \
             mock.patch('os.path.exists', return_value=False):
            with assert_logging([('fetch', 'foo from {}'.format(where))]):
                pkg.fetch(self.metadata, self.config)
            mtar.assert_called_once_with(srcdir, None)

    def test_url(self):
        pkg = self.make_package('foo', url=self.srcurl, build='bfg9000')
        builder = self.make_builder(Bfg9000Builder, pkg)
        self.assertEqual(pkg.url, self.srcurl)
        self.assertEqual(pkg.path, None)
        self.assertEqual(pkg.patch, None)
        self.assertEqual(pkg.builders, [builder])
        self.assertEqual(pkg.needs_dependencies, True)
        self.assertEqual(pkg.should_deploy, True)

        self.check_fetch(pkg)
        self.check_resolve(pkg)

    def test_path(self):
        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000')
        builder = self.make_builder(Bfg9000Builder, pkg)
        self.assertEqual(pkg.url, None)
        self.assertEqual(pkg.path, Path(self.srcpath))
        self.assertEqual(pkg.patch, None)
        self.assertEqual(pkg.builders, [builder])
        self.assertEqual(pkg.needs_dependencies, True)
        self.assertEqual(pkg.should_deploy, True)

        self.check_fetch(pkg)
        self.check_resolve(pkg)

    def test_zip_path(self):
        srcpath = os.path.join(test_data_dir, 'hello-bfg.zip')
        pkg = self.make_package('foo', build='bfg9000', path=srcpath)
        builder = self.make_builder(Bfg9000Builder, pkg)
        self.assertEqual(pkg.url, None)
        self.assertEqual(pkg.path, Path(srcpath))
        self.assertEqual(pkg.builders, [builder])
        self.assertEqual(pkg.needs_dependencies, True)
        self.assertEqual(pkg.should_deploy, True)

        srcdir = os.path.join(self.pkgdir, 'src', 'foo')
        with mock.patch('mopack.origins.sdist.urlopen', self.mock_urlopen), \
             mock.patch('zipfile.ZipFile.extractall') as mtar, \
             mock.patch('os.path.isdir', return_value=True), \
             mock.patch('os.path.exists', return_value=False):
            with assert_logging([('fetch', 'foo from {}'.format(srcpath))]):
                pkg.fetch(self.metadata, self.config)
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
        with mock.patch('mopack.origins.sdist.urlopen', self.mock_urlopen), \
             mock.patch('tarfile.TarFile.extractall') as mtar, \
             mock.patch('os.path.isdir', return_value=True), \
             mock.patch('os.path.exists', return_value=False):
            with assert_logging([('fetch',
                                  'foo from {}'.format(self.srcpath))]):
                pkg.fetch(self.metadata, self.config)
            mtar.assert_called_once_with(srcdir, mock.ANY)
        self.check_resolve(pkg)

    def test_patch(self):
        patch = os.path.join(test_data_dir, 'hello-bfg.patch')
        pkg = self.make_package('foo', path=self.srcpath, patch=patch,
                                build='bfg9000')
        self.assertEqual(pkg.patch, Path(patch))

        srcdir = os.path.join(self.pkgdir, 'src', 'foo')
        with mock.patch('mopack.origins.sdist.urlopen', self.mock_urlopen), \
             mock.patch('mopack.origins.sdist.pushd'), \
             mock.patch('tarfile.TarFile.extractall') as mtar, \
             mock.patch('os.path.isdir', return_value=True), \
             mock.patch('os.path.exists', return_value=False), \
             mock.patch('builtins.open', mock_open_after_first()) as mopen, \
             mock.patch('os.makedirs'), \
             mock.patch('mopack.log.LogFile.check_call') as mcall:
            with assert_logging([
                ('fetch', 'foo from {}'.format(self.srcpath)),
                ('patch', 'foo with {}'.format(patch)),
            ]):
                pkg.fetch(self.metadata, self.config)
            mtar.assert_called_once_with(srcdir, None)
            mcall.assert_called_once_with(['patch', '-p1'], stdin=mopen(),
                                          env={})
        self.check_resolve(pkg)

    def test_build(self):
        build = {'type': 'bfg9000', 'extra_args': '--extra'}
        pkg = self.make_package('foo', path=self.srcpath, build=build,
                                linkage='pkg_config')
        builder = self.make_builder(Bfg9000Builder, pkg, extra_args='--extra')
        self.assertEqual(pkg.path, Path(self.srcpath))
        self.assertEqual(pkg.builders, [builder])

        self.check_fetch(pkg)
        self.check_resolve(pkg)

    def test_infer_build(self):
        # Basic inference
        pkg = self.make_package('foo', path=self.srcpath)
        self.assertEqual(pkg.builders, None)

        with mock.patch('os.path.exists', mock_exists), \
             mock.patch('tarfile.TarFile.extractall'), \
             mock.patch('builtins.open', mock_open_after_first(
                 read_data='export:\n  build: bfg9000'
             )):
            with assert_logging([('fetch',
                                  'foo from {}'.format(self.srcpath))]):
                config = pkg.fetch(self.metadata, self.config)
            self.assertEqual(config.export.build, 'bfg9000')
            self.assertEqual(pkg, self.make_package(
                'foo', path=self.srcpath, build='bfg9000'
            ))
        self.check_resolve(pkg)

        # Infer but override linkage and version
        pkg = self.make_package('foo', path=self.srcpath,
                                linkage={'type': 'system'})
        self.assertEqual(pkg.builders, None)

        with mock.patch('os.path.exists', mock_exists), \
             mock.patch('tarfile.TarFile.extractall'), \
             mock.patch('builtins.open', mock_open_after_first(
                 read_data='export:\n  build: bfg9000'
             )):
            with assert_logging([('fetch',
                                  'foo from {}'.format(self.srcpath))]):
                config = pkg.fetch(self.metadata, self.config)
            self.assertEqual(config.export.build, 'bfg9000')
            self.assertEqual(pkg, self.make_package(
                'foo', path=self.srcpath, build='bfg9000',
                linkage={'type': 'system'}
            ))
        with mock.patch('subprocess.run', side_effect=OSError()), \
             mock.patch('mopack.linkages.path_system.PathLinkage._filter_path',
                        lambda *args: []), \
             mock.patch('mopack.linkages.path_system.file_outdated',
                        return_value=True), \
             mock.patch('os.makedirs'), \
             mock.patch('builtins.open'):
            self.check_resolve(pkg, linkage={
                'name': 'foo', 'type': 'system', 'generated': True,
                'auto_link': False, 'pcnames': ['foo'],
                'pkg_config_path': [self.pkgconfdir(None)],
            })

    def test_infer_build_override(self):
        pkg = self.make_package('foo', path=self.srcpath, build='cmake',
                                linkage='pkg_config')

        with mock.patch('os.path.exists', mock_exists), \
             mock.patch('tarfile.TarFile.extractall'), \
             mock.patch('builtins.open', mock_open_after_first(
                 read_data='export:\n  build: bfg9000'
             )):
            with assert_logging([('fetch',
                                  'foo from {}'.format(self.srcpath))]):
                config = pkg.fetch(self.metadata, self.config)
            self.assertEqual(config.export.build, 'bfg9000')
            self.assertEqual(pkg, self.make_package(
                'foo', path=self.srcpath, build='cmake', linkage='pkg_config'
            ))
        with mock.patch('mopack.builders.cmake.pushd'):
            self.check_resolve(pkg)

    def test_linkage(self):
        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                linkage='pkg_config')
        builder = self.make_builder(Bfg9000Builder, pkg)
        self.assertEqual(pkg.path, Path(self.srcpath))
        self.assertEqual(pkg.builders, [builder])

        self.check_fetch(pkg)
        self.check_resolve(pkg)

        with mock.patch('subprocess.run') as mrun:
            pkg.version(self.metadata)
            mrun.assert_called_once_with(
                ['pkg-config', 'foo', '--modversion'],
                check=True, env={'PKG_CONFIG_PATH': self.pkgconfdir('foo')},
                stdout=subprocess.PIPE, universal_newlines=True
            )

        linkage = {'type': 'pkg_config', 'pkg_config_path': 'pkgconf'}
        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                linkage=linkage)
        self.assertEqual(pkg.path, Path(self.srcpath))
        self.assertEqual(pkg.builders, [builder])

        self.check_fetch(pkg)
        self.check_resolve(pkg, linkage={
            'name': 'foo', 'type': 'pkg_config', 'pcnames': ['foo'],
            'pkg_config_path': [self.pkgconfdir('foo', 'pkgconf')],
        })

        linkage = {'type': 'path', 'libraries': []}
        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                linkage=linkage)
        self.assertEqual(pkg.path, Path(self.srcpath))
        self.assertEqual(pkg.builders, [builder])

        self.check_fetch(pkg)
        self.check_resolve(pkg, linkage={
            'name': 'foo', 'type': 'path', 'generated': True,
            'auto_link': False, 'pcnames': ['foo'],
            'pkg_config_path': [self.pkgconfdir(None)],
        })

        with mock.patch('subprocess.run') as mrun:
            self.assertEqual(pkg.version(self.metadata), None)
            mrun.assert_not_called()

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                submodules=submodules_required)
        self.check_fetch(pkg)
        self.check_resolve(pkg, submodules=['sub'])

        pkg = self.make_package(
            'foo', path=self.srcpath, build='bfg9000',
            linkage={'type': 'pkg_config', 'pcname': 'bar'},
            submodules=submodules_required
        )
        self.check_fetch(pkg)
        self.check_resolve(pkg, submodules=['sub'], linkage={
            'name': 'foo[sub]', 'type': 'pkg_config',
            'pcnames': ['bar', 'foo_sub'],
            'pkg_config_path': [self.pkgconfdir('foo')],
        })

        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                submodules=submodules_optional)
        self.check_fetch(pkg)
        self.check_resolve(pkg, submodules=['sub'])

        pkg = self.make_package(
            'foo', path=self.srcpath, build='bfg9000',
            linkage={'type': 'pkg_config', 'pcname': 'bar'},
            submodules=submodules_optional
        )
        self.check_fetch(pkg)
        self.check_resolve(pkg, submodules=['sub'], linkage={
            'name': 'foo[sub]', 'type': 'pkg_config',
            'pcnames': ['bar', 'foo_sub'],
            'pkg_config_path': [self.pkgconfdir('foo')],
        })

    def test_invalid_submodule(self):
        pkg = self.make_package(
            'foo', path=self.srcpath, build='bfg9000',
            submodules={'names': ['sub'], 'required': True}
        )
        with self.assertRaises(ValueError):
            pkg.get_linkage(self.metadata, ['invalid'])

    def test_already_fetched(self):
        def mock_exists(p):
            return os.path.basename(p) == 'foo'

        build = {'type': 'bfg9000', 'extra_args': '--extra'}
        pkg = self.make_package('foo', path=self.srcpath, srcdir='srcdir',
                                build=build, linkage='pkg_config')
        with mock.patch('os.path.exists', mock_exists), \
             mock.patch('tarfile.TarFile.extractall') as mtar, \
             mock.patch('os.path.isdir', return_value=True):
            with assert_logging([('fetch', 'foo already fetched')]):
                pkg.fetch(self.metadata, self.config)
            mtar.assert_not_called()
        self.check_resolve(pkg)

    def test_deploy(self):
        deploy_dirs = {'prefix': '/usr/local'}
        pkg = self.make_package('foo', url=self.srcurl, build='bfg9000',
                                deploy_dirs=deploy_dirs)
        self.assertEqual(pkg.should_deploy, True)
        self.check_fetch(pkg)

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('mopack.builders.ninja.pushd'), \
             mock.patch('mopack.log.LogFile.check_call') as mcall:
            with assert_logging([('resolve', 'foo')]):
                pkg.resolve(self.metadata)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'foo.log'
            ), 'a')
            builddir = os.path.join(self.pkgdir, 'build', 'foo')
            mcall.assert_any_call(
                ['bfg9000', 'configure', builddir, '--prefix', '/usr/local'],
                env={}
            )

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('mopack.builders.ninja.pushd'), \
             mock.patch('mopack.log.LogFile.check_call') as mcall:
            with assert_logging([('deploy', 'foo')]):
                pkg.deploy(self.metadata)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'deploy', 'foo.log'
            ), 'a')
            mcall.assert_any_call(['ninja', 'install'], env={})

        pkg = self.make_package('foo', url='http://example.com',
                                build='bfg9000', deploy=False)
        self.assertEqual(pkg.should_deploy, False)

        with mock_open_log() as mopen:
            pkg.deploy(self.metadata)
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
             mock.patch('shutil.rmtree') as mrmtree:
            self.assertEqual(oldpkg.clean_pre(self.metadata, oldpkg), False)
            mlog.assert_not_called()
            mrmtree.assert_not_called()

        # Tarball -> Tarball (different)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch('shutil.rmtree') as mrmtree:
            self.assertEqual(oldpkg.clean_pre(self.metadata, newpkg1), True)
            mlog.assert_called_once()
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

        # Tarball -> Apt
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch('shutil.rmtree') as mrmtree:
            self.assertEqual(oldpkg.clean_pre(self.metadata, newpkg2), True)
            mlog.assert_called_once()
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

        # Tarball -> nothing
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch('shutil.rmtree') as mrmtree:
            self.assertEqual(oldpkg.clean_pre(self.metadata, None), True)
            mlog.assert_called_once()
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

        # Tarball -> nothing (quiet)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch('shutil.rmtree') as mrmtree:
            self.assertEqual(oldpkg.clean_pre(self.metadata, None, True), True)
            mlog.assert_not_called()
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

    def test_clean_post(self):
        otherpath = os.path.join(test_data_dir, 'other_project.tar.gz')

        oldpkg = self.make_package('foo', path=self.srcpath,
                                   srcdir='bfg_project', build='bfg9000')
        newpkg1 = self.make_package('foo', path=otherpath, build='bfg9000')
        newpkg2 = self.make_package(AptPackage, 'foo')

        # Tarball -> Tarball (same)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:
            self.assertEqual(oldpkg.clean_post(self.metadata, oldpkg), False)
            mlog.assert_not_called()
            mclean.assert_not_called()

        # Tarball -> Tarball (different)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:
            self.assertEqual(oldpkg.clean_post(self.metadata, newpkg1), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.metadata, oldpkg)

        # Tarball -> Apt
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:
            self.assertEqual(oldpkg.clean_post(self.metadata, newpkg2), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.metadata, oldpkg)

        # Tarball -> nothing
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:
            self.assertEqual(oldpkg.clean_post(self.metadata, None), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.metadata, oldpkg)

        # Tarball -> nothing (quiet)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:
            self.assertEqual(oldpkg.clean_post(self.metadata, None, True),
                             True)
            mlog.assert_not_called()
            mclean.assert_called_once_with(self.metadata, oldpkg)

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
             mock.patch('shutil.rmtree') as mrmtree:
            self.assertEqual(oldpkg.clean_all(self.metadata, oldpkg),
                             (False, False))
            mlog.assert_not_called()
            mclean.assert_not_called()
            mrmtree.assert_not_called()

        # Tarball -> Tarball (different)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean, \
             mock.patch('shutil.rmtree') as mrmtree:
            self.assertEqual(oldpkg.clean_all(self.metadata, newpkg1),
                             (True, True))
            self.assertEqual(mlog.call_count, 2)
            mclean.assert_called_once_with(self.metadata, oldpkg)
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

        # Tarball -> Apt
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean, \
             mock.patch('shutil.rmtree') as mrmtree:
            self.assertEqual(oldpkg.clean_all(self.metadata, newpkg2),
                             (True, True))
            self.assertEqual(mlog.call_count, 2)
            mclean.assert_called_once_with(self.metadata, oldpkg)
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

        # Tarball -> nothing
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean, \
             mock.patch('shutil.rmtree') as mrmtree:
            self.assertEqual(oldpkg.clean_all(self.metadata, None),
                             (True, True))
            self.assertEqual(mlog.call_count, 2)
            mclean.assert_called_once_with(self.metadata, oldpkg)
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

        # Tarball -> nothing (quiet)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean, \
             mock.patch('shutil.rmtree') as mrmtree:
            self.assertEqual(oldpkg.clean_all(self.metadata, None, True),
                             (True, True))
            mlog.assert_not_called()
            mclean.assert_called_once_with(self.metadata, oldpkg)
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
        opts = self.make_options()
        pkg = TarballPackage('foo', path=self.srcpath, build='bfg9000',
                             _options=opts, config_file=self.config_file)
        data = through_json(pkg.dehydrate())
        self.assertEqual(pkg, Package.rehydrate(data, _options=opts))

        pkg = TarballPackage('foo', url=self.srcurl, build='bfg9000',
                             _options=opts, config_file=self.config_file)
        data = through_json(pkg.dehydrate())
        self.assertEqual(pkg, Package.rehydrate(data, _options=opts))

        pkg = TarballPackage('foo', path=self.srcpath, _options=opts,
                             config_file=self.config_file)
        with self.assertRaises(ConfigurationError):
            data = pkg.dehydrate()

    def test_upgrade(self):
        opts = self.make_options()
        data = {
            'origin': 'tarball', '_version': 0, 'name': 'foo',
            'path': {'base': 'cfgdir', 'path': 'foo.tar.gz'}, 'url': None,
            'files': [], 'srcdir': '.', 'patch': None,
            'builder': {'type': 'none', '_version': 1, 'name': 'foo'},
            'linkage': {'type': 'system', '_version': 1},
        }
        with mock.patch.object(TarballPackage, 'upgrade',
                               side_effect=TarballPackage.upgrade) as m:
            pkg = Package.rehydrate(data, _options=opts)
            self.assertIsInstance(pkg, TarballPackage)
            self.assertIsInstance(pkg.linkage, SystemLinkage)
            self.assertEqual([type(i) for i in pkg.builders], [NoneBuilder])
            m.assert_called_once()

    def test_builder_types(self):
        pkg = TarballPackage('foo', path=self.srcpath, build='bfg9000',
                             _options=self.make_options(),
                             config_file=self.config_file)
        self.assertEqual(pkg.builder_types, ['bfg9000'])

        pkg = TarballPackage('foo', path=self.srcpath,
                             _options=self.make_options(),
                             config_file=self.config_file)
        with self.assertRaises(ConfigurationError):
            pkg.builder_types
