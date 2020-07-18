import tarfile
import zipfile

__all__ = ['Archive', 'open']


class Archive:
    def __init__(self, file, mode='r:*'):
        split_mode = mode.split(':', 1)
        if len(split_mode) == 2:
            mode, fmt = split_mode
        else:
            mode, fmt = split_mode[0], '*'
        full_mode = mode + ':' + fmt

        if fmt == '*':
            is_zip = zipfile.is_zipfile(file)
            file.seek(0)

            if is_zip:
                self._archive = zipfile.ZipFile(file, mode)
            else:
                self._archive = tarfile.open(mode=full_mode, fileobj=file)
        elif fmt == 'zip':
            self._archive = zipfile.ZipFile(file, mode)
        else:
            self._archive = tarfile.open(mode=full_mode, fileobj=file)

    def __enter__(self):
        self._archive.__enter__()
        return self

    def __exit__(self, type, value, traceback):
        self._archive.__exit__(type, value, traceback)

    def getnames(self):
        def fixdir(info):
            if info.isdir() and info.name[-1] != '/':
                return info.name + '/'
            return info.name

        if isinstance(self._archive, zipfile.ZipFile):
            result = self._archive.namelist()
        else:
            result = [fixdir(i) for i in self._archive.getmembers()]
        result.sort()
        return result

    def extract(self, member, path='.'):
        return self._archive.extract(member, path)

    def extractall(self, path='.', members=None):
        return self._archive.extractall(path, members)


def open(*args, **kwargs):
    return Archive(*args, **kwargs)
