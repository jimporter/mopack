import os
import tarfile
from io import BytesIO
from urllib.request import urlopen

from . import Package
from ..builders import make_builder


class TarballPackage(Package):
    def __init__(self, name, *, build, url=None, path=None, files=None):
        super().__init__(name)

        if (url is None) == (path is None):
            raise TypeError('exactly one of `url` or `path` must be specified')
        self.url = url
        self.path = path
        self.files = files
        self.builder = make_builder(name, build)

    def fetch(self):
        f = (BytesIO(urlopen(self.url).read()) if self.url else
             open(self.path, 'rb'))
        # XXX: Support more than just gzip.
        with tarfile.open(mode='r:gz', fileobj=f) as tar:
            srcdir = tar.next().name.split('/', 1)[0]
            if self.files:
                for i in self.files:
                    tar.extract(i)
            else:
                tar.extractall()

        builddir = self.builder.build(srcdir)
        pkgconfig = os.path.join(builddir, 'pkgconfig')
        return {'usage': 'pkgconfig', 'path': pkgconfig}
