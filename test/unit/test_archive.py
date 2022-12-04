import os.path
import sys
from unittest import mock, TestCase

from .. import AlwaysEqual, test_data_dir

from mopack import archive


class TestTarArchive(TestCase):
    def test_create(self):
        f = mock.MagicMock()
        with mock.patch('tarfile.open') as mtar:
            archive.TarArchive(f, 'r:tar')
            mtar.assert_called_once_with(mode='r:tar', fileobj=f)

        with mock.patch('tarfile.open') as mtar, \
             mock.patch('zipfile.is_zipfile', return_value=False):
            archive.TarArchive(f, 'r:*')
            mtar.assert_called_once_with(mode='r:*', fileobj=f)

        with mock.patch('tarfile.open') as mtar, \
             mock.patch('zipfile.is_zipfile', return_value=False):
            archive.TarArchive(f, 'r')
            mtar.assert_called_once_with(mode='r', fileobj=f)

        with mock.patch('tarfile.open') as mtar, \
             mock.patch('zipfile.is_zipfile', return_value=False):
            archive.TarArchive(f)
            mtar.assert_called_once_with(mode='r:*', fileobj=f)

    def test_open(self):
        f = mock.MagicMock()
        with mock.patch('tarfile.open') as mtar:
            archive.open(f, 'r:tar')
            mtar.assert_called_once_with(mode='r:tar', fileobj=f)

        with mock.patch('tarfile.open') as mtar, \
             mock.patch('zipfile.is_zipfile', return_value=False):
            archive.open(f, 'r:*')
            mtar.assert_called_once_with(mode='r:*', fileobj=f)

        with mock.patch('tarfile.open') as mtar, \
             mock.patch('zipfile.is_zipfile', return_value=False):
            archive.open(f, 'r')
            mtar.assert_called_once_with(mode='r', fileobj=f)

        with mock.patch('tarfile.open') as mtar, \
             mock.patch('zipfile.is_zipfile', return_value=False):
            archive.open(f)
            mtar.assert_called_once_with(mode='r:*', fileobj=f)

    def test_with(self):
        f = mock.MagicMock()
        with mock.patch('tarfile.open'):
            with archive.open(f, 'r:tar'):
                pass

    def test_getnames(self):
        d = 'hello-bfg/'
        names = [d, d + 'build.bfg', d + 'include/', d + 'include/hello.hpp',
                 d + 'src/', d + 'src/hello.cpp']

        path = os.path.join(test_data_dir, 'hello-bfg.tar.gz')
        with open(path, 'rb') as f, archive.open(f, 'r:gz') as arc:
            self.assertEqual(arc.getnames(), names)

    def test_extract(self):
        f = mock.MagicMock()
        with mock.patch('tarfile.open') as mtar, \
             mock.patch('tarfile.TarFile', type(mtar())):
            with archive.open(f, 'r:tar') as arc:
                arc.extract('file.txt')
                arc.extract('file2.txt', 'path')
                arc.extract('dir/')
            mtar().extract.assert_has_calls([
                mock.call('file.txt', '.'),
                mock.call('file2.txt', 'path'),
                mock.call('dir', '.'),
            ])

    def test_extractall(self):
        f = mock.MagicMock()
        with mock.patch('tarfile.open') as mtar, \
             mock.patch('tarfile.TarFile', type(mtar())):
            with archive.open(f, 'r:tar') as arc:
                arc.extractall()
                arc.extractall('path')
                arc.extractall(members=['dir/', 'file.txt'])
            mtar().extractall.assert_has_calls([
                mock.call('.', None),
                mock.call('path', None),
                mock.call('.', AlwaysEqual())
            ])

            # Make our mock iterate over the members list we gave it. This
            # check only works with newer versions of Python though.
            if sys.version_info >= (3, 8):
                list(mtar().extractall.mock_calls[-1].args[1])
                self.assertEqual(
                    [i.args[0] for i in mtar().getmember.mock_calls],
                    ['dir', 'file.txt']
                )


class TestZipArchive(TestCase):
    def test_create(self):
        f = mock.MagicMock()
        with mock.patch('zipfile.ZipFile') as mzip:
            archive.ZipArchive(f, 'r:zip')
            mzip.assert_called_once_with(f, 'r')

        with mock.patch('zipfile.ZipFile') as mzip, \
             mock.patch('zipfile.is_zipfile', return_value=True):
            archive.ZipArchive(f, 'r:*')
            mzip.assert_called_once_with(f, 'r')

        with mock.patch('zipfile.ZipFile') as mzip, \
             mock.patch('zipfile.is_zipfile', return_value=True):
            archive.ZipArchive(f, 'r')
            mzip.assert_called_once_with(f, 'r')

        with mock.patch('zipfile.ZipFile') as mzip, \
             mock.patch('zipfile.is_zipfile', return_value=True):
            archive.ZipArchive(f)
            mzip.assert_called_once_with(f, 'r')

        with self.assertRaises(ValueError):
            archive.ZipArchive(f, 'r:gzip')

    def test_open(self):
        f = mock.MagicMock()
        with mock.patch('zipfile.ZipFile') as mzip:
            archive.open(f, 'r:zip')
            mzip.assert_called_once_with(f, 'r')

        with mock.patch('zipfile.ZipFile') as mzip, \
             mock.patch('zipfile.is_zipfile', return_value=True):
            archive.open(f, 'r:*')
            mzip.assert_called_once_with(f, 'r')

        with mock.patch('zipfile.ZipFile') as mzip, \
             mock.patch('zipfile.is_zipfile', return_value=True):
            archive.open(f, 'r')
            mzip.assert_called_once_with(f, 'r')

        with mock.patch('zipfile.ZipFile') as mzip, \
             mock.patch('zipfile.is_zipfile', return_value=True):
            archive.open(f)
            mzip.assert_called_once_with(f, 'r')

    def test_with(self):
        f = mock.MagicMock()
        with mock.patch('zipfile.ZipFile'):
            with archive.open(f, 'r:zip'):
                pass

    def test_getnames(self):
        d = 'hello-bfg/'
        names = [d, d + 'build.bfg', d + 'include/', d + 'include/hello.hpp',
                 d + 'src/', d + 'src/hello.cpp']

        path = os.path.join(test_data_dir, 'hello-bfg.zip')
        with open(path, 'rb') as f, archive.open(f, 'r:zip') as arc:
            self.assertEqual(arc.getnames(), names)

    def test_extract(self):
        f = mock.MagicMock()
        with mock.patch('zipfile.ZipFile') as mzip:
            with archive.open(f, 'r:zip') as arc:
                arc.extract('file.txt')
                arc.extract('file2.txt', 'path')
                arc.extract('dir/')
            mzip().extract.assert_has_calls([
                mock.call('file.txt', '.'),
                mock.call('file2.txt', 'path'),
                mock.call('dir/', '.'),
            ])

    def test_extractall(self):
        f = mock.MagicMock()
        with mock.patch('zipfile.ZipFile') as mzip:
            with archive.open(f, 'r:zip') as arc:
                arc.extractall()
                arc.extractall('path')
                arc.extractall(members=['dir/', 'file.txt'])
            mzip().extractall.assert_has_calls([
                mock.call('.', None),
                mock.call('path', None),
                mock.call('.', ['dir/', 'file.txt'])
            ])
