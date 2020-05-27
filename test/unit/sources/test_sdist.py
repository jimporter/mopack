import os
from unittest import mock

from . import SourceTest
from .. import mock_open_log
from ... import *

from mopack.builders.bfg9000 import Bfg9000Builder
from mopack.config import Config
from mopack.iterutils import iterate
from mopack.sources import Package
from mopack.sources.apt import AptPackage
from mopack.sources.sdist import DirectoryPackage, TarballPackage

mock_bfgclean = 'mopack.builders.bfg9000.Bfg9000Builder.clean'


def mock_open_after_first(*args, **kwargs):
    _open = open
    mock_open = mock.mock_open(*args, **kwargs)

    def non_mock(*args, **kwargs):
        mock_open.side_effect = None
        return _open(*args, **kwargs)

    mock_open.side_effect = non_mock
    return mock_open


class SDistTestCase(SourceTest):
    config_file = '/path/to/mopack.yml'
    pkgdir = '/path/to/builddir/mopack'
    deploy_paths = {'prefix': '/usr/local'}

    def pkgconfdir(self, name, pkgconfig='pkgconfig'):
        return os.path.join(self.pkgdir, 'build', name, pkgconfig)

    def check_resolve(self, pkg, *, submodules=None, usage=None):
        if usage is None:
            pcfiles = ([] if pkg.submodules and pkg.submodules['required'] else
                       ['foo'])
            pcfiles.extend('foo_{}'.format(i) for i in iterate(submodules))
            usage = {'type': 'pkg-config', 'path': self.pkgconfdir('foo'),
                     'pcfiles': pcfiles}

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('subprocess.check_call'):  # noqa
            pkg.resolve(self.pkgdir, self.deploy_paths)
            mopen.assert_called_with(os.path.join(self.pkgdir, 'foo.log'), 'w')
        self.assertEqual(pkg.get_usage(self.pkgdir, submodules), usage)

    def make_builder(self, builder_type, name, *, submodules=None, **kwargs):
        builder = builder_type(name, submodules=submodules, **kwargs)
        builder.set_options(self.make_options())
        return builder


class TestDirectory(SDistTestCase):
    pkg_type = DirectoryPackage
    srcpath = os.path.join(test_data_dir, 'hello-bfg')

    def test_resolve(self):
        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000')
        self.assertEqual(pkg.path, self.srcpath)
        self.assertEqual(pkg.builder, self.make_builder(Bfg9000Builder, 'foo'))

        pkg.fetch(self.pkgdir, None)
        self.check_resolve(pkg)

    def test_build(self):
        build = {'type': 'bfg9000', 'extra_args': '--extra'}
        pkg = self.make_package('foo', path=self.srcpath, build=build,
                                usage='pkg-config')
        self.assertEqual(pkg.path, self.srcpath)
        self.assertEqual(pkg.builder, self.make_builder(
            Bfg9000Builder, 'foo', extra_args='--extra'
        ))

        pkg.fetch(self.pkgdir, None)
        self.check_resolve(pkg)

    def test_infer_build(self):
        pkg = self.make_package('foo', path=self.srcpath, set_options=False)
        self.assertEqual(pkg.builder, None)

        with mock.patch('os.path.exists', return_value=True):
            config = pkg.fetch(self.pkgdir, Config([]))
            self.set_options(pkg)
            self.assertEqual(config.build, 'bfg9000')
            self.assertEqual(pkg.builder, self.make_builder(
                Bfg9000Builder, 'foo'
            ))
        self.check_resolve(pkg)

        pkg = self.make_package('foo', path=self.srcpath,
                                usage={'type': 'system'}, set_options=False)

        with mock.patch('os.path.exists', return_value=True):
            config = pkg.fetch(self.pkgdir, Config([]))
            self.set_options(pkg)
            self.assertEqual(config.build, 'bfg9000')
            self.assertEqual(pkg.builder, self.make_builder(
                Bfg9000Builder, 'foo', usage={'type': 'system'}
            ))
        self.check_resolve(pkg, usage={
            'type': 'system', 'include_path': [], 'library_path': [],
            'headers': [], 'libraries': ['foo']
        })

    def test_infer_submodules(self):
        srcpath = os.path.join(test_data_dir, 'hello-multi-bfg')
        pkg = self.make_package('foo', path=srcpath, set_options=False)
        self.assertEqual(pkg.builder, None)

        with mock.patch('os.path.exists', return_value=True):
            config = pkg.fetch(self.pkgdir, Config([]))
            self.set_options(pkg)
            self.assertEqual(config.build, 'bfg9000')
            self.assertEqual(config.submodules, ['french', 'english'])
            self.assertEqual(pkg.builder, self.make_builder(
                Bfg9000Builder, 'foo', submodules={
                    'names': ['french', 'english'], 'required': True
                }
            ))
        self.check_resolve(pkg, submodules=['french'])

        pkg = self.make_package('foo', path=srcpath, submodules=['sub'],
                                set_options=False)
        self.assertEqual(pkg.builder, None)

        with mock.patch('os.path.exists', return_value=True):
            config = pkg.fetch(self.pkgdir, Config([]))
            self.set_options(pkg)
            self.assertEqual(config.build, 'bfg9000')
            self.assertEqual(config.submodules, ['french', 'english'])
            self.assertEqual(pkg.builder, self.make_builder(
                Bfg9000Builder, 'foo', submodules={
                    'names': ['sub'], 'required': True
                }
            ))
        self.check_resolve(pkg, submodules=['sub'])

    def test_usage(self):
        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                usage='pkg-config')
        self.assertEqual(pkg.path, self.srcpath)
        self.assertEqual(pkg.builder, self.make_builder(
            Bfg9000Builder, 'foo', usage='pkg-config'
        ))

        pkg.fetch(self.pkgdir, None)
        self.check_resolve(pkg)

        usage = {'type': 'pkg-config', 'path': 'pkgconf'}
        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                usage=usage)
        self.assertEqual(pkg.path, self.srcpath)
        self.assertEqual(pkg.builder, self.make_builder(
            Bfg9000Builder, 'foo', usage=usage
        ))

        pkg.fetch(self.pkgdir, None)
        self.check_resolve(pkg, usage={
            'type': 'pkg-config', 'path': self.pkgconfdir('foo', 'pkgconf'),
            'pcfiles': ['foo']
        })

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                submodules=submodules_required)
        self.check_resolve(pkg, submodules=['sub'])

        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                usage={'type': 'pkg-config', 'pcfile': 'bar'},
                                submodules=submodules_required)
        self.check_resolve(pkg, submodules=['sub'], usage={
            'type': 'pkg-config', 'path': self.pkgconfdir('foo'),
            'pcfiles': ['bar', 'foo_sub']
        })

        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                submodules=submodules_optional)
        self.check_resolve(pkg, submodules=['sub'])

        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                usage={'type': 'pkg-config', 'pcfile': 'bar'},
                                submodules=submodules_optional)
        self.check_resolve(pkg, submodules=['sub'], usage={
            'type': 'pkg-config', 'path': self.pkgconfdir('foo'),
            'pcfiles': ['bar', 'foo_sub']
        })

    def test_invalid_submodule(self):
        pkg = self.make_package(
            'foo', path=self.srcpath, build='bfg9000',
            submodules={'names': ['sub'], 'required': True}
        )
        with self.assertRaises(ValueError):
            pkg.get_usage(self.pkgdir, ['invalid'])

    def test_deploy(self):
        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000')

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('subprocess.check_call'):  # noqa
            pkg.deploy(self.pkgdir)
            mopen.assert_called_with(
                os.path.join(self.pkgdir, 'foo-deploy.log'), 'w'
            )

    def test_clean_pre(self):
        oldpkg = self.make_package('foo', build='bfg9000', path=self.srcpath)
        newpkg = self.make_package(AptPackage, 'foo')

        # System -> Apt
        self.assertEqual(oldpkg.clean_pre(self.pkgdir, newpkg), False)

        # Apt -> nothing
        self.assertEqual(oldpkg.clean_pre(self.pkgdir, None), False)

    def test_clean_post(self):
        otherpath = os.path.join(test_data_dir, 'other_project')
        oldpkg = self.make_package('foo', build='bfg9000', path=self.srcpath)
        newpkg1 = self.make_package('foo', build='bfg9000', path=otherpath)
        newpkg2 = self.make_package(AptPackage, 'foo')

        # Directory -> Directory (same)
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, oldpkg), False)
            mlog.assert_not_called()
            mclean.assert_not_called()

        # Directory -> Directory (different)
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, newpkg1), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)

        # Directory -> Apt
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, newpkg2), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)

        # Directory -> nothing
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, None), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)

    def test_clean_all(self):
        otherpath = os.path.join(test_data_dir, 'other_project')
        oldpkg = self.make_package('foo', build='bfg9000', path=self.srcpath)
        newpkg1 = self.make_package('foo', build='bfg9000', path=otherpath)
        newpkg2 = self.make_package(AptPackage, 'foo')

        # Directory -> Directory (same)
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, oldpkg),
                             (False, False))
            mlog.assert_not_called()
            mclean.assert_not_called()

        # Directory -> Directory (different)
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, newpkg1),
                             (False, True))
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)

        # Directory -> Apt
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, newpkg2),
                             (False, True))
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)

        # Directory -> nothing
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, None),
                             (False, True))
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)

    def test_equality(self):
        otherpath = os.path.join(test_data_dir, 'other_project')
        pkg = self.make_package('foo', build='bfg9000', path=self.srcpath)

        self.assertEqual(pkg, self.make_package(
            'foo', build='bfg9000', path=self.srcpath
        ))
        self.assertEqual(pkg, self.make_package(
            'foo', build='bfg9000', path=self.srcpath
        ))

        self.assertNotEqual(pkg, self.make_package(
            'bar', build='bfg9000', path=self.srcpath
        ))
        self.assertNotEqual(pkg, self.make_package(
            'foo', build='bfg9000', path=otherpath,
        ))

    def test_rehydrate(self):
        pkg = DirectoryPackage('foo', build='bfg9000', path=self.srcpath,
                               config_file=self.config_file)
        data = pkg.dehydrate()
        self.assertNotIn('pending_usage', data)
        self.assertEqual(pkg, Package.rehydrate(data))

        pkg = DirectoryPackage('foo', path=self.srcpath,
                               config_file=self.config_file)
        with self.assertRaises(TypeError):
            data = pkg.dehydrate()


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
            mtar.assert_called_once_with(srcdir)

    def test_url(self):
        pkg = self.make_package('foo', build='bfg9000', url=self.srcurl)
        self.assertEqual(pkg.url, self.srcurl)
        self.assertEqual(pkg.path, None)
        self.assertEqual(pkg.builder, self.make_builder(Bfg9000Builder, 'foo'))

        self.check_fetch(pkg)
        self.check_resolve(pkg)

    def test_path(self):
        pkg = self.make_package('foo', build='bfg9000', path=self.srcpath)
        self.assertEqual(pkg.url, None)
        self.assertEqual(pkg.path, self.srcpath)
        self.assertEqual(pkg.builder, self.make_builder(Bfg9000Builder, 'foo'))

        self.check_fetch(pkg)
        self.check_resolve(pkg)

    def test_missing_url_path(self):
        with self.assertRaises(TypeError):
            self.make_package('foo', build='bfg9000')

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
        pkg = self.make_package('foo', path=self.srcpath, set_options=False)
        self.assertEqual(pkg.builder, None)

        with mock.patch('os.path.exists', return_value=True), \
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

        with mock.patch('os.path.exists', return_value=True), \
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
            'type': 'system', 'include_path': [], 'library_path': [],
            'headers': [], 'libraries': ['foo'],
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
            'pcfiles': ['foo']
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
            'pcfiles': ['bar', 'foo_sub']
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
            'pcfiles': ['bar', 'foo_sub']
        })

    def test_invalid_submodule(self):
        pkg = self.make_package(
            'foo', path=self.srcpath, build='bfg9000',
            submodules={'names': ['sub'], 'required': True}
        )
        with self.assertRaises(ValueError):
            pkg.get_usage(self.pkgdir, ['invalid'])

    def test_deploy(self):
        pkg = self.make_package('foo', build='bfg9000',
                                url='http://example.com')

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('subprocess.check_call'):  # noqa
            pkg.deploy(self.pkgdir)
            mopen.assert_called_with(
                os.path.join(self.pkgdir, 'foo-deploy.log'), 'w'
            )

    def test_clean_pre(self):
        otherpath = os.path.join(test_data_dir, 'other_project.tar.gz')

        oldpkg = self.make_package('foo', build='bfg9000', path=self.srcpath,
                                   srcdir='bfg_project')
        newpkg1 = self.make_package('foo', build='bfg9000', path=otherpath)
        newpkg2 = self.make_package(AptPackage, 'foo')

        srcdir = os.path.join(self.pkgdir, 'src', 'foo')

        # Tarball -> Tarball (same)
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch('shutil.rmtree') as mrmtree:  # noqa
            self.assertEqual(oldpkg.clean_pre(self.pkgdir, oldpkg), False)
            mlog.assert_not_called()
            mrmtree.assert_not_called()

        # Tarball -> Tarball (different)
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch('shutil.rmtree') as mrmtree:  # noqa
            self.assertEqual(oldpkg.clean_pre(self.pkgdir, newpkg1), True)
            mlog.assert_called_once()
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

        # Tarball -> Apt
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch('shutil.rmtree') as mrmtree:  # noqa
            self.assertEqual(oldpkg.clean_pre(self.pkgdir, newpkg2), True)
            mlog.assert_called_once()
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

        # Tarball -> nothing
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch('shutil.rmtree') as mrmtree:  # noqa
            self.assertEqual(oldpkg.clean_pre(self.pkgdir, None), True)
            mlog.assert_called_once()
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

    def test_clean_post(self):
        otherpath = os.path.join(test_data_dir, 'other_project.tar.gz')

        oldpkg = self.make_package('foo', build='bfg9000', path=self.srcpath,
                                   srcdir='bfg_project')
        newpkg1 = self.make_package('foo', build='bfg9000', path=otherpath)
        newpkg2 = self.make_package(AptPackage, 'foo')

        # Tarball -> Tarball (same)
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, oldpkg), False)
            mlog.assert_not_called()
            mclean.assert_not_called()

        # Tarball -> Tarball (different)
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, newpkg1), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)

        # Tarball -> Apt
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, newpkg2), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)

        # Tarball -> nothing
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, None), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)

    def test_clean_all(self):
        otherpath = os.path.join(test_data_dir, 'other_project.tar.gz')

        oldpkg = self.make_package('foo', build='bfg9000', path=self.srcpath,
                                   srcdir='bfg_project')
        newpkg1 = self.make_package('foo', build='bfg9000', path=otherpath)
        newpkg2 = self.make_package(AptPackage, 'foo')

        srcdir = os.path.join(self.pkgdir, 'src', 'foo')

        # Tarball -> Tarball (same)
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean, \
             mock.patch('shutil.rmtree') as mrmtree:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, oldpkg),
                             (False, False))
            mlog.assert_not_called()
            mclean.assert_not_called()
            mrmtree.assert_not_called()

        # Tarball -> Tarball (different)
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean, \
             mock.patch('shutil.rmtree') as mrmtree:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, newpkg1),
                             (True, True))
            self.assertEqual(mlog.call_count, 2)
            mclean.assert_called_once_with(self.pkgdir)
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

        # Tarball -> Apt
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean, \
             mock.patch('shutil.rmtree') as mrmtree:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, newpkg2),
                             (True, True))
            self.assertEqual(mlog.call_count, 2)
            mclean.assert_called_once_with(self.pkgdir)
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

        # Tarball -> nothing
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean, \
             mock.patch('shutil.rmtree') as mrmtree:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, None),
                             (True, True))
            self.assertEqual(mlog.call_count, 2)
            mclean.assert_called_once_with(self.pkgdir)
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

    def test_equality(self):
        otherpath = os.path.join(test_data_dir, 'other_project.tar.gz')
        pkg = self.make_package('foo', build='bfg9000', path=self.srcpath)

        self.assertEqual(pkg, self.make_package(
            'foo', build='bfg9000', path=self.srcpath
        ))
        self.assertEqual(pkg, self.make_package(
            'foo', build='bfg9000', path=self.srcpath,
            config_file='/path/to/mopack2.yml'
        ))

        self.assertNotEqual(pkg, self.make_package(
            'bar', build='bfg9000', path=self.srcpath
        ))
        self.assertNotEqual(pkg, self.make_package(
            'foo', build='bfg9000', url=self.srcurl
        ))
        self.assertNotEqual(pkg, self.make_package(
            'foo', build='bfg9000', path=otherpath
        ))

    def test_rehydrate(self):
        pkg = TarballPackage('foo', build='bfg9000', path=self.srcpath,
                             config_file=self.config_file)
        data = pkg.dehydrate()
        self.assertEqual(pkg, Package.rehydrate(data))

        pkg = TarballPackage('foo', path=self.srcpath,
                             config_file=self.config_file)
        with self.assertRaises(TypeError):
            data = pkg.dehydrate()
