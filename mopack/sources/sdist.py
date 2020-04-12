import os
import shutil
import tarfile
from io import BytesIO
from urllib.request import urlopen

from . import Package
from .. import log
from ..builders import Builder, make_builder


class SDistPackage(Package):
    _rehydrate_fields = {'builder': Builder}

    def __init__(self, name, *, build, **kwargs):
        super().__init__(name, **kwargs)
        self.builder = make_builder(name, build)

    def _find_mopack(self, srcdir):
        mopack = os.path.join(srcdir, 'mopack.yml')
        return mopack if os.path.exists(mopack) else None

    def clean_needed(self, pkgdir, new_package):
        if new_package == self:
            return False

        log.info('cleaning {!r}'.format(self.name))
        self.builder.clean(pkgdir)
        return True

    def _resolve(self, pkgdir, srcdir, deploy_paths):
        log.info('resolving {!r}'.format(self.name))

        builddir = self.builder.build(pkgdir, srcdir, deploy_paths)
        pkgconfig = os.path.join(builddir, 'pkgconfig')
        usage = {'type': 'pkgconfig', 'path': pkgconfig}
        return self._resolved_metadata(usage)

    def deploy(self, pkgdir):
        log.info('deploying {!r}'.format(self.name))
        self.builder.deploy(pkgdir)


class DirectoryPackage(SDistPackage):
    source = 'directory'

    def __init__(self, name, *, path, **kwargs):
        super().__init__(name, **kwargs)
        self.path = os.path.normpath(os.path.join(self.config_dir, path))

    def fetch(self, pkgdir):
        log.info('fetching {!r} from {}'.format(self.name, self.source))
        return self._find_mopack(self.path)

    def resolve(self, pkgdir, deploy_paths):
        return self._resolve(pkgdir, self.path, deploy_paths)


class TarballPackage(SDistPackage):
    source = 'tarball'
    _skip_compare_fields = (SDistPackage._skip_compare_fields +
                            ('guessed_srcdir',))

    def __init__(self, name, *, url=None, path=None, files=None, srcdir=None,
                 **kwargs):
        super().__init__(name, **kwargs)

        if (url is None) == (path is None):
            raise TypeError('exactly one of `url` or `path` must be specified')
        self.url = url
        self.path = (os.path.normpath(os.path.join(self.config_dir, path))
                     if path is not None else None)
        self.files = files
        self.srcdir = srcdir
        self.guessed_srcdir = None  # Set in fetch().

    def _srcdir(self, pkgdir):
        return os.path.join(pkgdir, 'src', self.srcdir or self.guessed_srcdir)

    def clean_needed(self, pkgdir, new_package):
        if super().clean_needed(pkgdir, new_package):
            shutil.rmtree(self._srcdir(pkgdir), ignore_errors=True)
            return True
        return False

    def fetch(self, pkgdir):
        log.info('fetching {!r} from {}'.format(self.name, self.source))

        base_srcdir = os.path.join(pkgdir, 'src')
        with (BytesIO(urlopen(self.url).read()) if self.url else
              open(self.path, 'rb')) as f:
            # XXX: Support more than just gzip.
            with tarfile.open(mode='r:gz', fileobj=f) as tar:
                self.guessed_srcdir = tar.next().name.split('/', 1)[0]
                if self.files:
                    for i in self.files:
                        tar.extract(i, base_srcdir)
                else:
                    tar.extractall(base_srcdir)

        return self._find_mopack(self.srcdir or self.guessed_srcdir)

    def resolve(self, pkgdir, deploy_paths):
        return self._resolve(pkgdir, self._srcdir(pkgdir), deploy_paths)
