from unittest import mock, TestCase

from mopack import archive


class TestArchive(TestCase):
    def test_open_tar(self):
        f = mock.MagicMock()
        with mock.patch('tarfile.open') as mtar:
            archive.open(f, 'r:tar')
            mtar.assert_called_once_with(mode='r:tar', fileobj=f)

        with mock.patch('tarfile.open') as mtar, \
             mock.patch('zipfile.is_zipfile', return_value=False):  # noqa
            archive.open(f, 'r:*')
            mtar.assert_called_once_with(mode='r:*', fileobj=f)

        with mock.patch('tarfile.open') as mtar, \
             mock.patch('zipfile.is_zipfile', return_value=False):  # noqa
            archive.open(f, 'r')
            mtar.assert_called_once_with(mode='r:*', fileobj=f)

        with mock.patch('tarfile.open') as mtar, \
             mock.patch('zipfile.is_zipfile', return_value=False):  # noqa
            archive.open(f)
            mtar.assert_called_once_with(mode='r:*', fileobj=f)

    def test_open_zip(self):
        f = mock.MagicMock()
        with mock.patch('zipfile.ZipFile') as mzip:
            archive.open(f, 'r:zip')
            mzip.assert_called_once_with(f, 'r')

        with mock.patch('zipfile.ZipFile') as mzip, \
             mock.patch('zipfile.is_zipfile', return_value=True):  # noqa
            archive.open(f, 'r:*')
            mzip.assert_called_once_with(f, 'r')

        with mock.patch('zipfile.ZipFile') as mzip, \
             mock.patch('zipfile.is_zipfile', return_value=True):  # noqa
            archive.open(f, 'r')
            mzip.assert_called_once_with(f, 'r')

        with mock.patch('zipfile.ZipFile') as mzip, \
             mock.patch('zipfile.is_zipfile', return_value=True):  # noqa
            archive.open(f)
            mzip.assert_called_once_with(f, 'r')

    def test_with(self):
        f = mock.MagicMock()
        with mock.patch('tarfile.open'):
            with archive.open(f, 'r:tar'):
                pass

    def test_getnames(self):
        f = mock.MagicMock()
        with mock.patch('tarfile.open') as mtar:
            with archive.open(f, 'r:tar') as arc:
                arc.getnames()
            mtar().getnames.assert_called_once_with()

        with mock.patch('zipfile.ZipFile') as mzip:
            with archive.open(f, 'r:zip') as arc:
                with mock.patch('zipfile.ZipFile', mock.MagicMock):
                    arc.getnames()
            mzip().namelist.assert_called_once_with()

    def test_extract(self):
        f = mock.MagicMock()
        with mock.patch('tarfile.open') as mtar:
            with archive.open(f, 'r:tar') as arc:
                arc.extract('file.txt')
                arc.extract('file2.txt', 'path')
            mtar().extract.assert_has_calls([
                mock.call('file.txt', '.'),
                mock.call('file2.txt', 'path'),
            ])

        with mock.patch('zipfile.ZipFile') as mzip:
            with archive.open(f, 'r:zip') as arc:
                arc.extract('file.txt')
                arc.extract('file2.txt', 'path')
            mzip().extract.assert_has_calls([
                mock.call('file.txt', '.'),
                mock.call('file2.txt', 'path'),
            ])

    def test_extractall(self):
        f = mock.MagicMock()
        with mock.patch('tarfile.open') as mtar:
            with archive.open(f, 'r:tar') as arc:
                arc.extractall()
                arc.extractall('path')
                arc.extractall(members=['file.txt'])
            mtar().extractall.assert_has_calls([
                mock.call('.', None),
                mock.call('path', None),
                mock.call('.', ['file.txt'])
            ])

        with mock.patch('zipfile.ZipFile') as mzip:
            with archive.open(f, 'r:zip') as arc:
                arc.extractall()
                arc.extractall('path')
                arc.extractall(members=['file.txt'])
            mzip().extractall.assert_has_calls([
                mock.call('.', None),
                mock.call('path', None),
                mock.call('.', ['file.txt'])
            ])
