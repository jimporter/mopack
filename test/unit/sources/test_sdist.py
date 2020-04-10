import os
from unittest import mock, TestCase

from .. import mock_open_log
from ... import *

from mopack.sources import Package
from mopack.sources.apt import AptPackage
from mopack.sources.sdist import DirectoryPackage, TarballPackage

mock_bfgclean = 'mopack.builders.bfg9000.Bfg9000Builder.clean'


def mock_open_after_first():
    _open = open
    mock_open = mock.mock_open()

    def non_mock(*args, **kwargs):
        mock_open.side_effect = None
        return _open(*args, **kwargs)

    mock_open.side_effect = non_mock
    return mock_open


class TestDirectory(TestCase):
    pkgdir = '/path/to/builddir/mopack'

    def test_path(self):
        path = os.path.join(test_data_dir, 'bfg_project')
        pkg = DirectoryPackage('foo', build='bfg9000', path=path,
                               config_file='/path/to/mopack.yml')
        self.assertEqual(pkg.path, path)

        pkg.fetch(self.pkgdir)

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('subprocess.check_call'):  # noqa
            pkg.resolve(self.pkgdir)
            mopen.assert_called_with(os.path.join(self.pkgdir, 'foo.log'), 'w')

    def test_clean(self):
        path1 = os.path.join(test_data_dir, 'bfg_project')
        path2 = os.path.join(test_data_dir, 'other_project')

        oldpkg = DirectoryPackage('foo', build='bfg9000', path=path1,
                                  config_file='/path/to/mopack.yml')
        newpkg1 = DirectoryPackage('foo', build='bfg9000', path=path2,
                                   config_file='/path/to/mopack.yml')
        newpkg2 = AptPackage('foo', config_file='/path/to/mopack.yml')

        # Directory -> Directory (same)
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_needed(self.pkgdir, oldpkg), False)
            mlog.assert_not_called()
            mclean.assert_not_called()

        # Directory -> Directory (different)
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_needed(self.pkgdir, newpkg1), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)

        # Directory -> Apt
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_needed(self.pkgdir, newpkg2), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)

        # Directory -> nothing
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_needed(self.pkgdir, None), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)

    def test_equality(self):
        path = os.path.join(test_data_dir, 'bfg_project')
        config_file = '/path/to/mopack.yml'
        pkg = DirectoryPackage('foo', build='bfg9000', path=path,
                               config_file=config_file)

        self.assertEqual(pkg, DirectoryPackage(
            'foo', build='bfg9000', path=path, config_file=config_file
        ))
        self.assertEqual(pkg, DirectoryPackage(
            'foo', build={'type': 'bfg9000', 'builddir': 'foo'}, path=path,
            config_file=config_file
        ))
        self.assertEqual(pkg, DirectoryPackage(
            'foo', build='bfg9000', path=path,
            config_file='/path/to/mopack2.yml'
        ))

        self.assertNotEqual(pkg, DirectoryPackage(
            'bar', build='bfg9000', path=path, config_file=config_file
        ))
        self.assertNotEqual(pkg, DirectoryPackage(
            'foo', build='bfg9000',
            path=os.path.join(test_data_dir, 'other_project'),
            config_file=config_file
        ))
        self.assertNotEqual(pkg, DirectoryPackage(
            'foo', build={'type': 'bfg9000', 'builddir': 'bar'}, path=path,
            config_file=config_file
        ))

    def test_rehydrate(self):
        path = os.path.join(test_data_dir, 'bfg_project')
        pkg = DirectoryPackage('foo', build='bfg9000', path=path,
                               config_file='/path/to/mopack.yml')
        data = pkg.dehydrate()
        self.assertEqual(pkg, Package.rehydrate(data))


class TestTarball(TestCase):
    pkgdir = '/path/to/builddir/mopack'

    def test_url(self):
        pkg = TarballPackage('foo', build='bfg9000', url='http://example.com',
                             config_file='/path/to/mopack.yml')
        self.assertEqual(pkg.url, 'http://example.com')
        self.assertEqual(pkg.path, None)

    def test_path(self):
        path = os.path.join(test_data_dir, 'bfg_project.tar.gz')
        pkg = TarballPackage('foo', build='bfg9000', path=path,
                             config_file='/path/to/mopack.yml')
        self.assertEqual(pkg.url, None)
        self.assertEqual(pkg.path, path)

        with mock.patch('tarfile.TarFile.extractall') as mtar:
            pkg.fetch(self.pkgdir)
            mtar.assert_called_once_with(os.path.join(self.pkgdir, 'src'))

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('subprocess.check_call'):  # noqa
            pkg.resolve(self.pkgdir)
            mopen.assert_called_with(os.path.join(self.pkgdir, 'foo.log'), 'w')

    def test_missing_url_path(self):
        with self.assertRaises(TypeError):
            TarballPackage('foo', build='bfg9000',
                           config_file='/path/to/mopack.yml')

    def test_clean(self):
        path1 = os.path.join(test_data_dir, 'bfg_project.tar.gz')
        path2 = os.path.join(test_data_dir, 'other_project.tar.gz')

        oldpkg = TarballPackage('foo', build='bfg9000', path=path1,
                                srcdir='bfg_project',
                                config_file='/path/to/mopack.yml')
        newpkg1 = TarballPackage('foo', build='bfg9000', path=path2,
                                 config_file='/path/to/mopack.yml')
        newpkg2 = AptPackage('foo', config_file='/path/to/mopack.yml')

        srcdir = os.path.join(self.pkgdir, 'src', 'bfg_project')

        # Tarball -> Tarball (same)
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean, \
             mock.patch('shutil.rmtree') as mrmtree:  # noqa
            self.assertEqual(oldpkg.clean_needed(self.pkgdir, oldpkg), False)
            mlog.assert_not_called()
            mclean.assert_not_called()
            mrmtree.assert_not_called()

        # Tarball -> Tarball (different)
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean, \
             mock.patch('shutil.rmtree') as mrmtree:  # noqa
            self.assertEqual(oldpkg.clean_needed(self.pkgdir, newpkg1), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

        # Tarball -> Apt
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean, \
             mock.patch('shutil.rmtree') as mrmtree:  # noqa
            self.assertEqual(oldpkg.clean_needed(self.pkgdir, newpkg2), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

        # Tarball -> nothing
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch(mock_bfgclean) as mclean, \
             mock.patch('shutil.rmtree') as mrmtree:  # noqa
            self.assertEqual(oldpkg.clean_needed(self.pkgdir, None), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

    def test_equality(self):
        path = os.path.join(test_data_dir, 'bfg_project.tar.gz')
        config_file = '/path/to/mopack.yml'
        pkg = TarballPackage('foo', build='bfg9000', path=path,
                             config_file=config_file)

        self.assertEqual(pkg, TarballPackage(
            'foo', build='bfg9000', path=path, config_file=config_file
        ))
        self.assertEqual(pkg, TarballPackage(
            'foo', build={'type': 'bfg9000', 'builddir': 'foo'}, path=path,
            config_file=config_file
        ))
        self.assertEqual(pkg, TarballPackage(
            'foo', build='bfg9000', path=path,
            config_file='/path/to/mopack2.yml'
        ))

        self.assertNotEqual(pkg, TarballPackage(
            'bar', build='bfg9000', path=path, config_file=config_file
        ))
        self.assertNotEqual(pkg, TarballPackage(
            'foo', build='bfg9000', url='http://example.com/project.tar.gz',
            config_file=config_file
        ))
        self.assertNotEqual(pkg, TarballPackage(
            'foo', build='bfg9000',
            path=os.path.join(test_data_dir, 'other_project.tar.gz'),
            config_file=config_file
        ))
        self.assertNotEqual(pkg, TarballPackage(
            'foo', build={'type': 'bfg9000', 'builddir': 'bar'}, path=path,
            config_file=config_file
        ))

    def test_rehydrate(self):
        path = os.path.join(test_data_dir, 'bfg_project.tar.gz')
        pkg = TarballPackage('foo', build='bfg9000', path=path,
                             config_file='/path/to/mopack.yml')
        data = pkg.dehydrate()
        self.assertEqual(pkg, Package.rehydrate(data))
