import os.path
from unittest import mock, TestCase

from .. import test_data_dir

from mopack import archive


class TestArchive(TestCase):
    def test_open_tar(self):
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
            mtar.assert_called_once_with(mode='r:*', fileobj=f)

        with mock.patch('tarfile.open') as mtar, \
             mock.patch('zipfile.is_zipfile', return_value=False):
            archive.open(f)
            mtar.assert_called_once_with(mode='r:*', fileobj=f)

    def test_open_zip(self):
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

        path = os.path.join(test_data_dir, 'hello-bfg.zip')
        with open(path, 'rb') as f, archive.open(f, 'r:zip') as arc:
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
        with mock.patch('tarfile.open') as mtar, \
             mock.patch('tarfile.TarFile', type(mtar())):
            with archive.open(f, 'r:tar') as arc:
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(arc)
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(arc, "path")
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(arc, members=["dir/", "file.txt"])
            mtar().extractall.assert_has_calls([
                mock.call('.', None),
                mock.call('path', None),
                mock.call('.', ['dir', 'file.txt'])
            ])

        with mock.patch('zipfile.ZipFile') as mzip:
            with archive.open(f, 'r:zip') as arc:
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(arc)
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(arc, "path")
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(arc, members=["dir/", "file.txt"])
            mzip().extractall.assert_has_calls([
                mock.call('.', None),
                mock.call('path', None),
                mock.call('.', ['dir/', 'file.txt'])
            ])
