import os
import shutil
import warnings
from io import BytesIO
from urllib.request import urlopen

from . import Package, submodules_type
from .. import archive, log, types
from ..builders import Builder, make_builder
from ..config import ChildConfig
from ..environment import get_cmd
from ..freezedried import GenericFreezeDried, ListFreezeDryer
from ..glob import filter_glob
from ..iterutils import flatten, isiterable
from ..linkages import make_linkage
from ..log import LogFile
from ..options import DuplicateSymbolError
from ..package_defaults import DefaultResolver
from ..path import Path, pushd
from ..types import FieldValueError
from ..yaml_tools import to_parse_error


@GenericFreezeDried.fields(rehydrate={'builders': ListFreezeDryer(Builder)},
                           skip_compare={'pending_linkage'})
class SDistPackage(Package):
    # TODO: Remove `usage` after v0.2 is released.
    def __init__(self, name, *, build=None, linkage=None,
                 usage=types.Unset, submodules=types.Unset,
                 inherit_defaults=True, _options, **kwargs):
        if linkage is None and usage is not types.Unset:
            warnings.warn(types.FieldKeyWarning(
                '`usage` is deprecated; use `linkage` instead', 'usage'
            ))
            linkage = usage

        super().__init__(name, inherit_defaults=inherit_defaults,
                         _options=_options, **kwargs)
        symbols = self._expr_symbols
        T = types.TypeCheck(locals(), symbols)

        if build is None:
            if submodules is not types.Unset:
                T.submodules(submodules_type)
            self.builders = None
            self.linkage = None
            self.pending_linkage = linkage
        else:
            pkg_default = DefaultResolver(self, symbols, inherit_defaults,
                                          name)
            T.submodules(pkg_default(submodules_type))
            self.builders = self._make_builders(build)
            self.linkage = self._make_linkage(linkage)

    def dehydrate(self):
        if hasattr(self, 'pending_linkage'):
            raise types.ConfigurationError(
                'cannot dehydrate until `pending_linkage` is finalized'
            )
        return super().dehydrate()

    @property
    def _builder_expr_symbols(self):
        return self._options.expr_symbols.augment(path_bases=['srcdir'])

    @property
    def _linkage_expr_symbols(self):
        path_bases = flatten(i.path_bases() for i in self.builders)
        return self._builder_expr_symbols.augment(path_bases=path_bases)

    @property
    def needs_dependencies(self):
        return True

    @property
    def builder_types(self):
        if self.builders is None:
            raise types.ConfigurationError(
                'cannot get builder types until builders are finalized'
            )
        return [i.type for i in self.builders]

    def path_values(self, metadata):
        srcdir = self._srcdir(metadata)
        values = {'srcdir': srcdir} if srcdir is not None else {}
        for i in self.builders:
            values.update(**i.path_values(metadata))
        return values

    def _make_builders(self, builders, **kwargs):
        path_owners = {}
        symbols = self._builder_expr_symbols

        def do_make(builder, field):
            nonlocal symbols
            try:
                result = make_builder(self, builder, _symbols=symbols,
                                      field=field, **kwargs)
                bases = result.path_bases()
                symbols = symbols.augment(path_bases=bases)
                path_owners.update({i: result for i in bases})
                return result
            except DuplicateSymbolError as e:
                msg = '{!r} already defined'.format(e.symbol)
                if e.symbol in path_owners:
                    msg += (' by {!r} builder'
                            .format(path_owners[e.symbol].type))
                raise FieldValueError(msg, field)

        if not isiterable(builders):
            return [do_make(builders, 'build')]
        else:
            return [do_make(builder, ('build', i))
                    for i, builder in enumerate(builders)]

    def _make_linkage(self, linkage, **kwargs):
        for i in self.builders:
            linkage = i.filter_linkage(linkage)
        return make_linkage(self, linkage, _symbols=self._linkage_expr_symbols,
                            **kwargs)

    def _find_mopack(self, parent_config, srcdir):
        config = ChildConfig([srcdir], parent_config=parent_config,
                             parent_package=self)

        if self.builders:
            return config

        if not config or not config.export:
            raise types.ConfigurationError((
                'build for package {!r} is not fully defined and package ' +
                'has no exported config'
            ).format(self.name))
        export = config.export

        if not hasattr(self, 'submodules'):
            with to_parse_error(export.config_file):
                self.submodules = submodules_type('submodules',
                                                  export.submodules)

        context = 'while constructing package {!r}'.format(self.name)
        with to_parse_error(export.config_file):
            with types.try_load_config(export.data, context, self.origin):
                self.builders = self._make_builders(export.build)

        if not self.pending_linkage and export.linkage:
            with to_parse_error(export.config_file):
                with types.try_load_config(export.data, context, self.origin):
                    self.linkage = self._make_linkage(export.linkage)
        else:
            # Note: If this fails and `pending_linkage` is a string, this won't
            # report any line number information for the error, since we've
            # lost that info by now in that case.
            with to_parse_error(self.config_file):
                with types.try_load_config(self.pending_linkage, context,
                                           self.origin):
                    self.linkage = self._make_linkage(self.pending_linkage,
                                                      field=None)

        del self.pending_linkage
        return config

    def clean_post(self, metadata, new_package, quiet=False):
        if self == new_package:
            return False

        if not quiet:
            log.pkg_clean(self.name)
        for i in self.builders:
            i.clean(metadata, self)
        return True

    def resolve(self, metadata):
        log.pkg_resolve(self.name)
        for i in self.builders:
            i.build(metadata, self)
        self.resolved = True

    def deploy(self, metadata):
        if self.should_deploy:
            log.pkg_deploy(self.name)
            if self.builders:
                self.builders[-1].deploy(metadata, self)


@GenericFreezeDried.fields(rehydrate={'path': Path})
class DirectoryPackage(SDistPackage):
    origin = 'directory'
    _version = 2

    @staticmethod
    def upgrade(config, version):
        # v2 adds support for multiple builders
        if version < 2:  # pragma: no branch
            config['builders'] = [config.pop('builder')]
        return config

    def __init__(self, name, *, path, **kwargs):
        super().__init__(name, **kwargs)

        T = types.TypeCheck(locals(), self._expr_symbols)
        T.path(types.any_path('cfgdir'))

    def _srcdir(self, metadata):
        return self.path.string({'cfgdir': self.config_dir})

    def fetch(self, metadata, parent_config):
        path = self.path.string({'cfgdir': self.config_dir})
        log.pkg_fetch(self.name, 'from {}'.format(path))
        return self._find_mopack(parent_config, path)


@GenericFreezeDried.fields(rehydrate={'path': Path},
                           skip_compare={'guessed_srcdir'})
class TarballPackage(SDistPackage):
    origin = 'tarball'
    _version = 2

    @staticmethod
    def upgrade(config, version):
        # v2 adds support for multiple builders
        if version < 2:  # pragma: no branch
            config['builders'] = [config.pop('builder')]
        return config

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

    def _base_srcdir(self, metadata):
        return os.path.join(metadata.pkgdir, 'src', self.name)

    def _srcdir(self, metadata):
        srcdir = self.srcdir or self.guessed_srcdir
        if srcdir is not None:
            return os.path.join(self._base_srcdir(metadata), srcdir)
        return None

    def _urlopen(self, url):
        with urlopen(url) as f:
            return BytesIO(f.read())

    def clean_pre(self, metadata, new_package, quiet=False):
        if self.equal(new_package, skip_fields={'builder'}):
            # Since both package objects have the same configuration, pass the
            # guessed srcdir on to the new package instance. That way, we don't
            # have to re-extract the tarball to get the guessed srcdir.
            new_package.guessed_srcdir = self.guessed_srcdir
            return False

        if not quiet:
            log.pkg_clean(self.name, 'sources')
        shutil.rmtree(self._base_srcdir(metadata), ignore_errors=True)
        return True

    def fetch(self, metadata, parent_config):
        base_srcdir = self._base_srcdir(metadata)
        if os.path.exists(base_srcdir):
            log.pkg_fetch(self.name, 'already fetched')
        else:
            path_bases = {'cfgdir': self.config_dir}
            where = self.url or self.path.string(path_bases)
            log.pkg_fetch(self.name, 'from {}'.format(where))

            with (self._urlopen(self.url) if self.url else
                  open(self.path.string(path_bases), 'rb')) as f:
                with archive.open(f) as arc:
                    names = arc.getnames()
                    self.guessed_srcdir = (names[0].split('/', 1)[0] if names
                                           else None)
                    if self.files:
                        # XXX: This doesn't extract parents of our globs, so
                        # owners/permissions won't be applied to them...
                        filtered = filter_glob(self.files, names)
                        arc.extractall(base_srcdir, members=filtered)
                    else:
                        arc.extractall(base_srcdir)

            if self.patch:
                env = self._common_options.env
                patch_cmd = get_cmd(env, 'PATCH', 'patch')
                patch = self.patch.string(path_bases)
                log.pkg_patch(self.name, 'with {}'.format(patch))
                with LogFile.open(metadata.pkgdir, self.name) as logfile, \
                     open(patch) as f, \
                     pushd(self._srcdir(metadata)):
                    logfile.check_call(patch_cmd + ['-p1'], stdin=f, env=env)

        return self._find_mopack(parent_config, self._srcdir(metadata))


class GitPackage(SDistPackage):
    origin = 'git'
    _version = 2

    @staticmethod
    def upgrade(config, version):
        # v2 adds support for multiple builders
        if version < 2:  # pragma: no branch
            config['builders'] = [config.pop('builder')]
        return config

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

    def _base_srcdir(self, metadata):
        return os.path.join(metadata.pkgdir, 'src', self.name)

    def _srcdir(self, metadata):
        return os.path.join(self._base_srcdir(metadata), self.srcdir)

    def clean_pre(self, metadata, new_package, quiet=False):
        if self.equal(new_package, skip_fields={'builder'}):
            return False

        if not quiet:
            log.pkg_clean(self.name, 'sources')
        shutil.rmtree(self._base_srcdir(metadata), ignore_errors=True)
        return True

    def fetch(self, metadata, parent_config):
        base_srcdir = self._base_srcdir(metadata)
        env = self._common_options.env
        git = get_cmd(env, 'GIT', 'git')

        with LogFile.open(metadata.pkgdir, self.name) as logfile:
            if os.path.exists(base_srcdir):
                if self.rev[0] == 'branch':
                    with pushd(base_srcdir):
                        logfile.check_call(git + ['pull'], env=env)
            else:
                log.pkg_fetch(self.name, 'from {}'.format(self.repository))
                clone = ['git', 'clone', self.repository, base_srcdir]
                if self.rev[0] in ['branch', 'tag']:
                    clone.extend(['--branch', self.rev[1]])
                    logfile.check_call(clone, env=env)
                elif self.rev[0] == 'commit':
                    logfile.check_call(clone, env=env)
                    with pushd(base_srcdir):
                        logfile.check_call(git + ['checkout', self.rev[1]],
                                           env=env)
                else:  # pragma: no cover
                    raise ValueError('unknown revision type {!r}'
                                     .format(self.rev[0]))

        return self._find_mopack(parent_config, self._srcdir(metadata))
