import os
import shutil
import tarfile
from io import BytesIO
from urllib.request import urlopen

from . import Package
from .. import log, types
from ..builders import Builder, make_builder
from ..config import ChildConfig


class SDistPackage(Package):
    _rehydrate_fields = {'builder': Builder}
    _skip_compare_fields = (Package._skip_compare_fields +
                            ('pending_usage',))

    def __init__(self, name, *, build=None, usage=None, **kwargs):
        super().__init__(name, **kwargs)
        if build is None:
            self.builder = None
            self.pending_usage = usage
        else:
            self.builder = make_builder(name, build, usage=usage)

    @property
    def builder_types(self):
        if self.builder is None:
            raise TypeError('cannot get builder types until builder is ' +
                            'finalized')
        return [self.builder.type]

    def set_options(self, options):
        super().set_options(options)
        self.builder.set_options(options)

    def dehydrate(self):
        if hasattr(self, 'pending_usage'):
            raise TypeError('cannot dehydrate until `pending_usage` is ' +
                            'finalized')
        return super().dehydrate()

    def _find_mopack(self, srcdir, parent_config):
        mopack = os.path.join(srcdir, 'mopack.yml')
        if os.path.exists(mopack):
            config = ChildConfig([mopack], parent=parent_config)
            if self.builder is None:
                usage = self.pending_usage or config.usage
                self.builder = make_builder(self.name, config.build,
                                            usage=usage)
                del self.pending_usage
            return config
        return None

    def clean_post(self, pkgdir, new_package):
        if self == new_package:
            return False

        log.info('cleaning {!r}'.format(self.name))
        self.builder.clean(pkgdir)
        return True

    def _resolve(self, pkgdir, srcdir, deploy_paths):
        log.info('resolving {!r}'.format(self.name))

        usage = self.builder.build(pkgdir, srcdir, deploy_paths)
        return self._resolved_metadata(usage)

    def deploy(self, pkgdir):
        log.info('deploying {!r}'.format(self.name))
        self.builder.deploy(pkgdir)


class DirectoryPackage(SDistPackage):
    source = 'directory'

    def __init__(self, name, *, path, **kwargs):
        super().__init__(name, **kwargs)
        self.path = types.any_path(self.config_dir)('path', path)

    def fetch(self, pkgdir, parent_config):
        log.info('fetching {!r} from {}'.format(self.name, self.source))
        return self._find_mopack(self.path, parent_config)

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
        self.path = types.maybe(types.any_path(self.config_dir))('path', path)
        self.files = files
        self.srcdir = types.maybe(types.inner_path)('srcdir', srcdir)
        self.guessed_srcdir = None  # Set in fetch().

    def _base_srcdir(self, pkgdir):
        return os.path.join(pkgdir, 'src', self.name)

    def _srcdir(self, pkgdir):
        return os.path.join(self._base_srcdir(pkgdir),
                            self.srcdir or self.guessed_srcdir)

    def _urlopen(self, url):
        with urlopen(url) as f:
            return BytesIO(f.read())

    def clean_pre(self, pkgdir, new_package):
        if self.equal(new_package, skip_fields=('builder', 'global_options')):
            return False

        log.info('cleaning {!r} sources'.format(self.name))
        shutil.rmtree(self._base_srcdir(pkgdir), ignore_errors=True)
        return True

    def fetch(self, pkgdir, parent_config):
        log.info('fetching {!r} from {}'.format(self.name, self.source))

        base_srcdir = self._base_srcdir(pkgdir)
        with (self._urlopen(self.url) if self.url else
              open(self.path, 'rb')) as f:
            # XXX: Support zip.
            with tarfile.open(mode='r:*', fileobj=f) as tar:
                self.guessed_srcdir = tar.next().name.split('/', 1)[0]
                if self.files:
                    for i in self.files:
                        tar.extract(i, base_srcdir)
                else:
                    tar.extractall(base_srcdir)

        return self._find_mopack(self.srcdir or self.guessed_srcdir,
                                 parent_config)

    def resolve(self, pkgdir, deploy_paths):
        return self._resolve(pkgdir, self._srcdir(pkgdir), deploy_paths)
