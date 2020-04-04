import os
import tarfile
from io import BytesIO
from urllib.request import urlopen

from . import Package
from ..builders import make_builder


class SDistPackage(Package):
    def __init__(self, name, *, build):
        super().__init__(name)
        self.builder = make_builder(name, build)

    def _build(self, srcdir):
        builddir = self.builder.build(srcdir)
        pkgconfig = os.path.join(builddir, 'pkgconfig')
        return {'usage': 'pkgconfig', 'path': pkgconfig}


class DirectoryPackage(SDistPackage):
    def __init__(self, name, *, path, **kwargs):
        super().__init__(name, **kwargs)
        self.path = path

    def fetch(self):
        return self._build(self.path)


class TarballPackage(SDistPackage):
    def __init__(self, name, *, url=None, path=None, files=None, **kwargs):
        super().__init__(name, **kwargs)

        if (url is None) == (path is None):
            raise TypeError('exactly one of `url` or `path` must be specified')
        self.url = url
        self.path = path
        self.files = files

    def fetch(self):
        with (BytesIO(urlopen(self.url).read()) if self.url else
              open(self.path, 'rb')) as f:
            # XXX: Support more than just gzip.
            with tarfile.open(mode='r:gz', fileobj=f) as tar:
                srcdir = tar.next().name.split('/', 1)[0]
                if self.files:
                    for i in self.files:
                        tar.extract(i)
                else:
                    tar.extractall()

        return self._build(srcdir)
