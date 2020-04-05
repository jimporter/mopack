import os
import tarfile
from io import BytesIO
from urllib.request import urlopen

from . import Package
from ..builders import make_builder


class SDistPackage(Package):
    def __init__(self, name, *, build, **kwargs):
        super().__init__(name, **kwargs)
        self.builder = make_builder(name, build)

    def _build(self, pkgdir, srcdir):
        builddir = self.builder.build(pkgdir, srcdir)
        pkgconfig = os.path.join(builddir, 'pkgconfig')
        return {'usage': 'pkgconfig', 'path': pkgconfig}


class DirectoryPackage(SDistPackage):
    def __init__(self, name, *, path, **kwargs):
        super().__init__(name, **kwargs)
        self.path = os.path.join(self.config_dir, path)

    def fetch(self, pkgdir):
        return self._build(pkgdir, self.path)


class TarballPackage(SDistPackage):
    def __init__(self, name, *, url=None, path=None, files=None, srcdir=None,
                 **kwargs):
        super().__init__(name, **kwargs)

        if (url is None) == (path is None):
            raise TypeError('exactly one of `url` or `path` must be specified')
        self.url = url
        self.path = (os.path.join(self.config_dir, path)
                     if path is not None else None)
        self.srcdir = srcdir
        self.files = files

    def fetch(self, pkgdir):
        srcdir = self.srcdir
        with (BytesIO(urlopen(self.url).read()) if self.url else
              open(self.path, 'rb')) as f:
            # XXX: Support more than just gzip.
            with tarfile.open(mode='r:gz', fileobj=f) as tar:
                if srcdir is None:
                    srcdir = tar.next().name.split('/', 1)[0]
                if self.files:
                    for i in self.files:
                        tar.extract(i, pkgdir)
                else:
                    tar.extractall(pkgdir)

        return self._build(pkgdir, os.path.join(pkgdir, srcdir))
