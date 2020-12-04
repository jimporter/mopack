import os
import shutil
from io import BytesIO
from urllib.request import urlopen

from . import Package, submodules_type
from .. import archive, log, types
from ..builders import Builder, make_builder
from ..config import ChildConfig
from ..freezedried import FreezeDried
from ..log import LogFile
from ..package_defaults import DefaultResolver
from ..path import filter_glob, pushd
from ..usage import make_usage
from ..yaml_tools import to_parse_error


@FreezeDried.fields(rehydrate={'builder': Builder},
                    skip_compare={'pending_usage'})
class SDistPackage(Package):
    def __init__(self, name, *, build=None, usage=None, submodules=types.Unset,
                 symbols, **kwargs):
        super().__init__(name, **kwargs)
        if build is None:
            self.builder = None
            self.pending_usage = usage
            self.pending_symbols = symbols
            if submodules is not types.Unset:
                self.submodules = submodules_type('submodules', submodules)
        else:
            package_default = DefaultResolver(self, symbols)
            self.submodules = package_default(submodules_type)(
                'submodules', submodules
            )
            if usage is not None:
                usage = make_usage(name, usage, submodules=self.submodules,
                                   symbols=symbols)
            self.builder = make_builder(name, build, usage=usage,
                                        submodules=self.submodules,
                                        symbols=symbols)

    @property
    def builder_types(self):
        if self.builder is None:
            raise types.ConfigurationError(
                'cannot get builder types until builder is finalized'
            )
        return [self.builder.type]

    def set_options(self, options):
        self.builder.set_options(options)
        super().set_options(options)

    def dehydrate(self):
        if hasattr(self, 'pending_usage'):
            raise types.ConfigurationError(
                'cannot dehydrate until `pending_usage` is finalized'
            )
        return super().dehydrate()

    def _find_mopack(self, srcdir, parent_config):
        config = ChildConfig([srcdir], parent=parent_config)
        if self.builder:
            return config

        if not config or not config.export:
            raise types.ConfigurationError((
                'build for package {!r} is not fully defined and package ' +
                'has no exported config'
            ).format(self.name))
        export = config.export

        if hasattr(self, 'submodules'):
            submodules = self.submodules
        if not hasattr(self, 'submodules'):
            with to_parse_error(export.config_file):
                submodules = submodules_type('submodules', export.submodules)

        kwargs = {'submodules': submodules, 'symbols': self.pending_symbols}
        if self.pending_usage:
            # XXX: This doesn't report any useful error message if it fails,
            # since we've lost the line numbers from the YAML file by now. One
            # option would be to separate make_usage() from applying submodules
            # so that we can call make_usage() in __init__() above.
            usage = make_usage(self.name, self.pending_usage, **kwargs)
        elif export.usage:
            with to_parse_error(export.config_file):
                with types.try_load_config(export.data, 'context', 'kind'):
                    usage = make_usage(self.name, export.usage, **kwargs)
        else:
            usage = None

        with to_parse_error(export.config_file):
            with types.try_load_config(export.data, 'context', 'kind'):
                self.builder = make_builder(self.name, export.build,
                                            usage=usage, **kwargs)

        if not hasattr(self, 'submodules'):
            self.submodules = submodules
        del self.pending_symbols
        del self.pending_usage
        return config

    def clean_post(self, pkgdir, new_package, quiet=False):
        if self == new_package:
            return False

        if not quiet:
            log.pkg_clean(self.name)
        self.builder.clean(pkgdir)
        return True

    def _resolve(self, pkgdir, srcdir, deploy_paths):
        log.pkg_resolve(self.name)
        self.builder.build(pkgdir, srcdir, deploy_paths)
        self.resolved = True

    def deploy(self, pkgdir):
        if self.should_deploy:
            log.pkg_deploy(self.name)
            self.builder.deploy(pkgdir)


class DirectoryPackage(SDistPackage):
    source = 'directory'

    def __init__(self, name, *, path, **kwargs):
        super().__init__(name, **kwargs)
        self.path = types.any_path(self.config_dir)('path', path)

    def fetch(self, pkgdir, parent_config):
        log.pkg_fetch(self.name, 'from {}'.format(self.path))
        return self._find_mopack(self.path, parent_config)

    def resolve(self, pkgdir, deploy_paths):
        return self._resolve(pkgdir, self.path, deploy_paths)

    def _get_usage(self, pkgdir, submodules):
        return self.builder.get_usage(pkgdir, submodules, self.path)


@FreezeDried.fields(skip_compare={'guessed_srcdir'})
class TarballPackage(SDistPackage):
    source = 'tarball'

    def __init__(self, name, *, path=None, url=None, files=None, srcdir=None,
                 patch=None, **kwargs):
        super().__init__(name, **kwargs)

        if (path is None) == (url is None):
            raise TypeError('exactly one of `path` or `url` must be specified')
        self.path = types.maybe(types.any_path(self.config_dir))('path', path)
        self.url = types.maybe(types.url)('url', url)
        self.files = types.list_of(types.string, listify=True)('files', files)
        self.srcdir = types.maybe(types.inner_path)('srcdir', srcdir)
        self.patch = types.maybe(types.any_path(self.config_dir))(
            'patch', patch
        )
        self.guessed_srcdir = None  # Set in fetch().

    def _base_srcdir(self, pkgdir):
        return os.path.join(pkgdir, 'src', self.name)

    def _srcdir(self, pkgdir):
        return os.path.join(self._base_srcdir(pkgdir),
                            self.srcdir or self.guessed_srcdir)

    def _urlopen(self, url):
        with urlopen(url) as f:
            return BytesIO(f.read())

    def clean_pre(self, pkgdir, new_package, quiet=False):
        if self.equal(new_package, skip_fields={'builder'}):
            # Since both package objects have the same configuration, pass the
            # guessed srcdir on to the new package instance. That way, we don't
            # have to re-extract the tarball to get the guessed srcdir.
            new_package.guessed_srcdir = self.guessed_srcdir
            return False

        if not quiet:
            log.pkg_clean(self.name, 'sources')
        shutil.rmtree(self._base_srcdir(pkgdir), ignore_errors=True)
        return True

    def fetch(self, pkgdir, parent_config):
        base_srcdir = self._base_srcdir(pkgdir)
        if os.path.exists(base_srcdir):
            log.pkg_fetch(self.name, 'already fetched')
        else:
            where = self.url or self.path
            log.pkg_fetch(self.name, 'from {}'.format(where))

            with (self._urlopen(self.url) if self.url else
                  open(self.path, 'rb')) as f:
                with archive.open(f) as arc:
                    names = arc.getnames()
                    self.guessed_srcdir = (names[0].split('/', 1)[0] if names
                                           else None)
                    if self.files:
                        # XXX: This doesn't extract parents of our globs, so
                        # owners/permissions won't be applied to them...
                        for i in filter_glob(self.files, names):
                            arc.extract(i, base_srcdir)
                    else:
                        arc.extractall(base_srcdir)

            if self.patch:
                log.pkg_patch(self.name, 'with {}'.format(self.patch))
                with LogFile.open(pkgdir, self.name) as logfile, \
                     open(self.patch) as f, \
                     pushd(self._srcdir(pkgdir)):  # noqa
                    logfile.check_call(['patch', '-p1'], stdin=f)

        return self._find_mopack(self._srcdir(pkgdir), parent_config)

    def resolve(self, pkgdir, deploy_paths):
        return self._resolve(pkgdir, self._srcdir(pkgdir), deploy_paths)

    def _get_usage(self, pkgdir, submodules):
        return self.builder.get_usage(pkgdir, submodules, self._srcdir(pkgdir))


class GitPackage(SDistPackage):
    source = 'git'

    def __init__(self, name, *, repository, tag=None, branch=None, commit=None,
                 srcdir='.', **kwargs):
        super().__init__(name, **kwargs)
        self.repository = types.one_of(
            types.url, types.ssh_path, types.any_path(self.config_dir),
            desc='a repository'
        )('repository', repository)

        rev = {'tag': tag, 'branch': branch, 'commit': commit}
        if sum(0 if i is None else 1 for i in rev.values()) > 1:
            raise TypeError('only one of `tag`, `branch`, or `commit` may ' +
                            'be specified')
        for k in rev:
            rev[k] = types.maybe(types.string)(k, rev[k])
        for k, v in rev.items():
            if v is not None:
                self.rev = [k, v]
                break
        else:
            self.rev = ['branch', 'master']

        self.srcdir = types.maybe(types.inner_path)('srcdir', srcdir)

    def _base_srcdir(self, pkgdir):
        return os.path.join(pkgdir, 'src', self.name)

    def _srcdir(self, pkgdir):
        return os.path.join(self._base_srcdir(pkgdir), self.srcdir)

    def clean_pre(self, pkgdir, new_package, quiet=False):
        if self.equal(new_package, skip_fields={'builder'}):
            return False

        if not quiet:
            log.pkg_clean(self.name, 'sources')
        shutil.rmtree(self._base_srcdir(pkgdir), ignore_errors=True)
        return True

    def fetch(self, pkgdir, parent_config):
        base_srcdir = self._base_srcdir(pkgdir)
        with LogFile.open(pkgdir, self.name) as logfile:
            if os.path.exists(base_srcdir):
                if self.rev[0] == 'branch':
                    with pushd(base_srcdir):
                        logfile.check_call(['git', 'pull'])
            else:
                log.pkg_fetch(self.name, 'from {}'.format(self.repository))
                clone = ['git', 'clone', self.repository, base_srcdir]
                if self.rev[0] in ['branch', 'tag']:
                    clone.extend(['--branch', self.rev[1]])
                    logfile.check_call(clone)
                elif self.rev[0] == 'commit':
                    logfile.check_call(clone)
                    with pushd(base_srcdir):
                        logfile.check_call(['git', 'checkout', self.rev[1]])
                else:  # pragma: no cover
                    raise ValueError('unknown revision type {!r}'
                                     .format(self.rev[0]))

        return self._find_mopack(self._srcdir(pkgdir), parent_config)

    def resolve(self, pkgdir, deploy_paths):
        return self._resolve(pkgdir, self._srcdir(pkgdir), deploy_paths)

    def _get_usage(self, pkgdir, submodules):
        return self.builder.get_usage(pkgdir, submodules, self._srcdir(pkgdir))
