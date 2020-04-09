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

    def _find_mopack(self, srcdir):
        mopack = os.path.join(srcdir, 'mopack.yml')
        return mopack if os.path.exists(mopack) else None

    def _build(self, pkgdir, srcdir):
        builddir = self.builder.build(pkgdir, srcdir)
        pkgconfig = os.path.join(builddir, 'pkgconfig')
        return {'type': 'pkgconfig', 'path': pkgconfig}


class DirectoryPackage(SDistPackage):
    def __init__(self, name, *, path, **kwargs):
        super().__init__(name, **kwargs)
        self.path = os.path.join(self.config_dir, path)

    def fetch(self, pkgdir):
        return self._find_mopack(self.path)

    def resolve(self, pkgdir):
        usage = self._build(pkgdir, self.path)
        return {'source': 'directory', 'usage': usage}


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
        base_srcdir = os.path.join(pkgdir, 'src')
        with (BytesIO(urlopen(self.url).read()) if self.url else
              open(self.path, 'rb')) as f:
            # XXX: Support more than just gzip.
            with tarfile.open(mode='r:gz', fileobj=f) as tar:
                # XXX: Should we be manipulating this object here, or should it
                # be frozen by the time we call fetch()?
                if self.srcdir is None:
                    self.srcdir = tar.next().name.split('/', 1)[0]
                if self.files:
                    for i in self.files:
                        tar.extract(i, base_srcdir)
                else:
                    tar.extractall(base_srcdir)

        return self._find_mopack(self.srcdir)

    def resolve(self, pkgdir):
        base_srcdir = os.path.join(pkgdir, 'src')
        usage = self._build(pkgdir, os.path.join(base_srcdir, self.srcdir))
        return {'source': 'tarball', 'usage': usage}
