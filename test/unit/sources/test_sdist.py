import os
from unittest import mock, TestCase

from ... import *

from mopack.sources.sdist import DirectoryPackage, TarballPackage


def mock_open_after_first():
    _open = open
    mock_open = mock.mock_open()

    def non_mock(*args, **kwargs):
        mock_open.side_effect = None
        return _open(*args, **kwargs)

    mock_open.side_effect = non_mock
    return mock_open


class TestDirectory(TestCase):
    def test_path(self):
        path = os.path.join(test_data_dir, 'bfg_project')
        pkg = DirectoryPackage('foo', build='bfg9000', path=path)
        self.assertEqual(pkg.path, path)

        with mock.patch('builtins.open', mock.mock_open()) as m, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('subprocess.check_call'):  # noqa
            pkg.fetch()
            m.assert_called_with('foo.log', 'w')


class TestTarball(TestCase):
    def test_url(self):
        p = TarballPackage('foo', build='bfg9000', url='http://example.com')
        self.assertEqual(p.url, 'http://example.com')
        self.assertEqual(p.path, None)

    def test_path(self):
        path = os.path.join(test_data_dir, 'bfg_project.tar.gz')
        pkg = TarballPackage('foo', build='bfg9000', path=path)
        self.assertEqual(pkg.url, None)
        self.assertEqual(pkg.path, path)

        with mock.patch('builtins.open', mock_open_after_first()) as mo, \
             mock.patch('tarfile.TarFile.extractall') as mt, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('subprocess.check_call'):  # noqa
            pkg.fetch()
            mo.assert_called_with('foo.log', 'w')

    def test_missing_url_path(self):
        with self.assertRaises(TypeError):
            TarballPackage('foo', build='bfg9000')
