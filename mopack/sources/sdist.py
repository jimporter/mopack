import os
import shutil
from io import BytesIO
from urllib.request import urlopen

from . import Package, submodules_type
from .. import archive, log, types
from ..builders import Builder, make_builder
from ..config import ChildConfig
from ..environment import get_cmd
from ..freezedried import FreezeDried
from ..glob import filter_glob
from ..log import LogFile
from ..package_defaults import DefaultResolver
from ..path import Path, pushd
from ..yaml_tools import to_parse_error


@FreezeDried.fields(rehydrate={'builder': Builder},
                    skip_compare={'pending_usage'})
class SDistPackage(Package):
    @staticmethod
    def upgrade(config, version):
        return config

    def __init__(self, name, *, build=None, usage=None, submodules=types.Unset,
                 _options, **kwargs):
        super().__init__(name, _options=_options, **kwargs)
        if build is None:
            if submodules is not types.Unset:
                self.submodules = submodules_type('submodules', submodules)
            self.builder = None
            self.pending_usage = usage
        else:
            package_default = DefaultResolver(self, _options.expr_symbols)
            self.submodules = package_default(submodules_type)(
                'submodules', submodules
            )
            self.builder = make_builder(
                name, build, submodules=self.submodules,
                _options=_options
            )
            self.builder.set_usage(usage, submodules=self.submodules)

    @property
    def needs_dependencies(self):
        return True

    @property
    def builder_types(self):
        if self.builder is None:
            raise types.ConfigurationError(
                'cannot get builder types until builder is finalized'
            )
        return [self.builder.type]

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

        context = 'while constructing package {!r}'.format(self.name)
        with to_parse_error(export.config_file):
            with types.try_load_config(export.data, context, self.source):
                builder = make_builder(self.name, export.build,
                                       submodules=submodules,
                                       _options=self._options)

        if not self.pending_usage and export.usage:
            with to_parse_error(export.config_file):
                with types.try_load_config(export.data, context, self.source):
                    builder.set_usage(export.usage, submodules=submodules)
        else:
            # Note: If this fails and `pending_usage` is a string, this won't
            # report any line number information for the error, since we've
            # lost that info in by now in that case.
            with to_parse_error(self.config_file):
                with types.try_load_config(self.pending_usage, context,
                                           self.source):
                    builder.set_usage(self.pending_usage, field=None,
                                      submodules=submodules)

        self.builder = builder
        if not hasattr(self, 'submodules'):
            self.submodules = submodules
        del self.pending_usage
        return config

    def clean_post(self, pkgdir, new_package, quiet=False):
        if self == new_package:
            return False

        if not quiet:
            log.pkg_clean(self.name)
        self.builder.clean(pkgdir)
        return True

    def resolve(self, pkgdir):
        log.pkg_resolve(self.name)
        self.builder.build(pkgdir, self._srcdir(pkgdir))
        self.resolved = True

    def deploy(self, pkgdir):
        if self.should_deploy:
            log.pkg_deploy(self.name)
            self.builder.deploy(pkgdir, self._srcdir(pkgdir))


@FreezeDried.fields(rehydrate={'path': Path})
class DirectoryPackage(SDistPackage):
    source = 'directory'
    _version = 1

    def __init__(self, name, *, path, **kwargs):
        super().__init__(name, **kwargs)

        T = types.TypeCheck(locals(), self._expr_symbols)
        T.path(types.any_path('cfgdir'))

    def _srcdir(self, pkgdir):
        return self.path.string(cfgdir=self.config_dir)

    def fetch(self, pkgdir, parent_config):
        path = self.path.string(cfgdir=self.config_dir)
        log.pkg_fetch(self.name, 'from {}'.format(path))
        return self._find_mopack(path, parent_config)

    def _get_usage(self, pkgdir, submodules):
        path = self.path.string(cfgdir=self.config_dir)
        return self.builder.get_usage(pkgdir, submodules, path)


@FreezeDried.fields(rehydrate={'path': Path}, skip_compare={'guessed_srcdir'})
class TarballPackage(SDistPackage):
    source = 'tarball'
    _version = 1

    def __init__(self, name, *, path=None, url=None, files=None, srcdir=None,
                 patch=None, **kwargs):
        super().__init__(name, **kwargs)

        T = types.TypeCheck(locals(), self._expr_symbols)
        T.path(types.maybe(types.any_path('cfgdir')))
        T.url(types.maybe(types.url))
        T.files(types.list_of(types.string, listify=True))
        T.srcdir(types.maybe(types.path_fragment))
        T.patch(types.maybe(types.any_path('cfgdir')))

        if (self.path is None) == (self.url is None):
            raise TypeError('exactly one of `path` or `url` must be specified')
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
            where = self.url or self.path.string(cfgdir=self.config_dir)
            log.pkg_fetch(self.name, 'from {}'.format(where))

            with (self._urlopen(self.url) if self.url else
                  open(self.path.string(cfgdir=self.config_dir), 'rb')) as f:
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
                patch_cmd = get_cmd(self._common_options.env, 'PATCH', 'patch')
                patch = self.patch.string(cfgdir=self.config_dir)
                log.pkg_patch(self.name, 'with {}'.format(patch))
                with LogFile.open(pkgdir, self.name) as logfile, \
                     open(patch) as f, \
                     pushd(self._srcdir(pkgdir)):  # noqa
                    logfile.check_call(patch_cmd + ['-p1'], stdin=f)

        return self._find_mopack(self._srcdir(pkgdir), parent_config)

    def _get_usage(self, pkgdir, submodules):
        return self.builder.get_usage(pkgdir, submodules, self._srcdir(pkgdir))


class GitPackage(SDistPackage):
    source = 'git'
    _version = 1

    def __init__(self, name, *, repository, tag=None, branch=None, commit=None,
                 srcdir='.', **kwargs):
        super().__init__(name, **kwargs)

        T = types.TypeCheck(locals(), self._expr_symbols)
        T.repository(types.one_of(
            types.url, types.ssh_path, types.any_path('cfgdir'),
            desc='a repository'
        ))
        T.srcdir(types.maybe(types.path_fragment))

        rev = {}
        T.tag(types.maybe(types.string), dest=rev)
        T.branch(types.maybe(types.string), dest=rev)
        T.commit(types.maybe(types.string), dest=rev)

        rev = {'tag': tag, 'branch': branch, 'commit': commit}
        if sum(0 if i is None else 1 for i in rev.values()) > 1:
            raise TypeError('only one of `tag`, `branch`, or `commit` may ' +
                            'be specified')
        for k, v in rev.items():
            if v is not None:
                self.rev = [k, v]
                break
        else:
            self.rev = ['branch', 'master']

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
        git = get_cmd(self._common_options.env, 'GIT', 'git')

        with LogFile.open(pkgdir, self.name) as logfile:
            if os.path.exists(base_srcdir):
                if self.rev[0] == 'branch':
                    with pushd(base_srcdir):
                        logfile.check_call(git + ['pull'])
            else:
                log.pkg_fetch(self.name, 'from {}'.format(self.repository))
                clone = ['git', 'clone', self.repository, base_srcdir]
                if self.rev[0] in ['branch', 'tag']:
                    clone.extend(['--branch', self.rev[1]])
                    logfile.check_call(clone)
                elif self.rev[0] == 'commit':
                    logfile.check_call(clone)
                    with pushd(base_srcdir):
                        logfile.check_call(git + ['checkout', self.rev[1]])
                else:  # pragma: no cover
                    raise ValueError('unknown revision type {!r}'
                                     .format(self.rev[0]))

        return self._find_mopack(self._srcdir(pkgdir), parent_config)

    def _get_usage(self, pkgdir, submodules):
        return self.builder.get_usage(pkgdir, submodules, self._srcdir(pkgdir))
