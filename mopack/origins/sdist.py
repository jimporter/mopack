import os
import shutil
import warnings
from contextlib import contextmanager
from io import BytesIO
from typing import Dict, List, Union
from urllib.request import urlopen
from subprocess import SubprocessError

from . import (dependencies_type, Package, submodules_type,
               submodule_required_type)
from .. import archive, log, types
from ..builders import Builder, make_builder
from ..config import ChildConfig
from ..dependencies import Dependency
from ..environment import get_cmd
from ..freezedried import GenericFreezeDried
from ..glob import filter_glob
from ..iterutils import flatten, isiterable, ismapping, iterate, listify
from ..linkages import make_linkage
from ..log import LogFile
from ..objutils import Unset
from ..options import DuplicateSymbolError
from ..package_defaults import DefaultResolver
from ..path import Path, pushd
from ..placeholder import MaybePlaceholderString
from ..types import FieldValueError
from ..yaml_tools import to_parse_error


@GenericFreezeDried.fields(rehydrate={
    'dependencies': List[Dependency],
    'env': Dict[str, MaybePlaceholderString],
    # FIXME: This is a mess.
    'submodules': Union[str, Dict[str, Dict[str, List[Dependency]]]],
    'builders': List[Builder]
}, skip_compare={'pkg_default', 'pending_builders', 'pending_linkage'})
class SDistPackage(Package):
    # TODO: Remove `usage` after v0.2 is released.
    def __init__(self, name, *, env=None, dependencies=Unset, submodules=Unset,
                 submodule_required=Unset, build=Unset, linkage=Unset,
                 usage=Unset, inherit_defaults=False, _options, **kwargs):
        # TODO: Remove this after v0.2 is released.
        if ( ismapping(submodules) and
             set(submodules.keys()) == {'names', 'required'} ):
            warnings.warn(types.FieldKeyWarning(
                ('`submodules` now takes a dictionary of submodules; use ' +
                 '`submodule_required` to set whether submodules are ' +
                 'required instead'), 'submodules'
            ))
            require_submodule = submodules.get('required', True)
            submodules = {i: {} for i in submodules['names']}

        if linkage is None and usage is not Unset:
            warnings.warn(types.FieldKeyWarning(
                '`usage` is deprecated; use `linkage` instead', 'usage'
            ))
            linkage = usage

        super().__init__(name, inherit_defaults=inherit_defaults,
                         _options=_options, **kwargs)

        self.pkg_default = DefaultResolver(self, self._expr_symbols,
                                           inherit_defaults, name)

        T = types.TypeCheck(locals(), self._expr_symbols)
        T.env(types.maybe(types.dict_of(
            types.string, types.placeholder_string
        ), default={}))

        self._expr_symbols = self._expr_symbols.augment(env=self.env)
        T = types.TypeCheck(locals(), self._expr_symbols)
        T.dependencies(types.maybe_raw(dependencies_type, empty=(Unset,)))
        T.submodules(submodules_type(raw=True))
        T.submodule_required(submodule_required_type(
            self.submodules, raw=True
        ))

        self.pending_builders = build
        self.pending_linkage = linkage

    @property
    def _finalized(self):
        return (not hasattr(self, 'pkg_default') and
                not hasattr(self, 'pending_builders') and
                not hasattr(self, 'pending_linkage'))

    def dehydrate(self):
        if not self._finalized:
            raise types.ConfigurationError(
                'cannot dehydrate until package is finalized'
            )
        return super().dehydrate()

    @GenericFreezeDried.rehydrator
    def rehydrate(cls, config, rehydrate_parent, **kwargs):
        # We need to rehydrate the builders after the basics of the package are
        # rehydrated, but *before* rehydrating linkage.
        builders_cfg = config.pop('builders')

        def after(pkg):
            pkg._expr_symbols = pkg._expr_symbols.augment(env=pkg.env)
            pkg.builders = [Builder.rehydrate(
                i, name=config['name'], _symbols=pkg._builder_expr_symbols,
                **kwargs
            ) for i in builders_cfg]
            return pkg

        return rehydrate_parent(SDistPackage, config, _after_rehydrate=after,
                                **kwargs)

    @property
    def _builder_expr_symbols(self):
        return self._expr_symbols.augment(path_bases=['srcdir'])

    @property
    def _linkage_expr_symbols(self):
        path_bases = flatten(i.path_bases() for i in self.builders)
        return self._builder_expr_symbols.augment(path_bases=path_bases)

    @property
    def needs_dependencies(self):
        return True

    @property
    def builder_types(self):
        if not self._finalized:
            raise types.ConfigurationError(
                'cannot get builder types until package is finalized'
            )
        return [i.type for i in self.builders]

    def path_values(self, metadata, *, with_builders=True):
        result = super().path_values(metadata)

        srcdir = self._srcdir(metadata)
        if srcdir:
            result['srcdir'] = srcdir

        if with_builders:
            for i in self.builders:
                result.update(**i.path_values(metadata, result))
        return result

    def _make_builders(self, builders, *, field='build', **kwargs):
        path_owners = {}
        symbols = self._builder_expr_symbols
        field = listify(field)

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

        if builders is Unset:
            builders = None
        if not isiterable(builders):
            return [do_make(builders, field)]
        else:
            return [do_make(builder, field + [i])
                    for i, builder in enumerate(builders)]

    def _make_linkage(self, linkage, **kwargs):
        if linkage is Unset:
            linkage = None
        for i in self.builders:
            linkage = i.filter_linkage(linkage)
        return make_linkage(self, linkage, _symbols=self._linkage_expr_symbols,
                            **kwargs)

    def _find_mopack(self, parent_config, srcdir):
        config = ChildConfig([srcdir], parent_config=parent_config,
                             parent_package=self)

        if config and config.export:
            export = config.export
        elif self.pending_builders is Unset:
            raise types.ConfigurationError((
                'build for package {!r} is not fully defined and package ' +
                'has no exported config'
            ).format(self.name))
        else:
            export = ChildConfig.Export({}, None)

        context = 'while constructing package {!r}'.format(self.name)

        @contextmanager
        def load_config(filename, data):
            with to_parse_error(filename):
                with types.try_load_config(data, context, self.origin):
                    yield

        T = types.TypeCheck(export, dest=self)
        recheck = (self.submodules is Unset and
                   self.submodule_required is not Unset)
        with load_config(export.config_file, export.data):
            if self.submodules is Unset:
                T.submodules(self.pkg_default(submodules_type(),
                                              default=Unset))
            if self.submodule_required is Unset:
                T.submodule_required(self.pkg_default(
                    submodule_required_type(self.submodules), default=Unset
                ))

            if self.dependencies is Unset:
                # TODO: Some way of automatically determining dependencies with
                # only the necessary submodules would be nice. This probably
                # requires some significant changes to package listings, e.g.
                # making the key be the package + submodule, and then having
                # some way to go to the "parent" dependency, i.e. the whole
                # package.
                default_deps = list(config.packages.keys()) if config else []
                T.dependencies(self.pkg_default(
                    dependencies_type, default=default_deps
                ))

        if recheck:
            # Re-check the `submodule_required` field for consistency.
            submodule_required_type(self.submodules)(
                'submodule_required', self.submodule_required
            )

        # TODO: Support package defaults for builders/linkage?

        # Construct the builders from the exported mopack config.
        if self.pending_builders is Unset and export.build:
            with load_config(export.config_file, export.data):
                self.builders = self._make_builders(export.build)
        else:
            # NOTE: If this fails and `pending_builders` is a string, this
            # won't report any line number information for the error, since
            # we've lost that info by now in that case.
            with load_config(self.config_file, self.pending_builders):
                self.builders = self._make_builders(self.pending_builders,
                                                    field=None)

        # Construct the linkage from the exported mopack config.
        if self.pending_linkage is Unset and export.linkage:
            with load_config(export.config_file, export.data):
                self.linkage = self._make_linkage(export.linkage)
        else:
            # NOTE: As above, this won't report any line number information for
            # errors if `pending_linage` is a string.
            with load_config(self.config_file, self.pending_linkage):
                self.linkage = self._make_linkage(self.pending_linkage,
                                                  field=None)

        del self.pkg_default
        del self.pending_builders
        del self.pending_linkage
        return config

    def _needs_clean(self, new_package):
        # We need to clean this package if there are any differences. Unset
        # optional fields aren't real differences though: they get filled in by
        # the package itself.
        return not self.equal(new_package, optional_fields={
            'dependencies', 'builders', 'linkage', 'submodules'
        })

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
        super().resolve(metadata)

    def deploy(self, metadata):
        if self.should_deploy:
            log.pkg_deploy(self.name)
            if self.builders:
                self.builders[-1].deploy(metadata, self)

    def get_dependencies(self, submodules):
        # Managed binary packages handle dependencies on their own, so mopack
        # has no need to define dependencies for them as well.
        dependencies = self.dependencies[:]
        if self.submodules != '*':
            for i in iterate(self._check_submodules(submodules)):
                dependencies.extend(self.submodules[i]['dependencies'])
        return dependencies


@GenericFreezeDried.fields(rehydrate={'path': Path})
class DirectoryPackage(SDistPackage):
    origin = 'directory'
    _version = 4

    @staticmethod
    def upgrade(config, version):
        # v2 adds support for multiple builders.
        if version < 2:  # pragma: no branch
            config['builders'] = [config.pop('builder')]

        # v3 adds the `env` field.
        if version < 3:  # pragma: no branch
            config['env'] = {}

        # v4 moves `submodules.required` to `submodule_required` and stores
        # `submodules` as a dict of submodule names.
        if version < 4:
            if config['submodules']:
                config['submodule_required'] = config['submodules']['required']
                config['submodules'] = {
                    i: {} for i in config['submodules']['names']
                }

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
    _version = 4

    @staticmethod
    def upgrade(config, version):
        # v2 adds support for multiple builders.
        if version < 2:  # pragma: no branch
            config['builders'] = [config.pop('builder')]

        # v3 adds the `env` field.
        if version < 3:  # pragma: no branch
            config['env'] = {}

        # v4 moves `submodules.required` to `submodule_required` and stores
        # `submodules` as a dict of submodule names.
        if version < 4:
            if config['submodules']:
                config['submodule_required'] = config['submodules']['required']
                config['submodules'] = {
                    i: {} for i in config['submodules']['names']
                }

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
        if not self._needs_clean(new_package):
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
        try:
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
                        self.guessed_srcdir = (names[0].split('/', 1)[0]
                                               if names else None)
                        if self.files:
                            # XXX: This doesn't extract parents of our globs,
                            # so owners/permissions won't be applied to them...
                            filtered = filter_glob(self.files, names)
                            arc.extractall(base_srcdir, members=filtered)
                        else:
                            arc.extractall(base_srcdir)

                if self.patch:
                    env = self._expr_symbols['env'].value(
                        self.path_values(metadata, with_builders=False)
                    )
                    patch_cmd = get_cmd(env, 'PATCH', 'patch')
                    patch = self.patch.string(path_bases)
                    log.pkg_patch(self.name, 'with {}'.format(patch))
                    with LogFile.open(metadata.pkgdir, self.name) as logfile, \
                         open(patch) as f, \
                         pushd(self._srcdir(metadata)):
                        logfile.check_call(patch_cmd + ['-p1'], stdin=f,
                                           env=env)
            return self._find_mopack(parent_config, self._srcdir(metadata))
        except SubprocessError:
            self._find_mopack(parent_config, self._srcdir(metadata))
            raise


class GitPackage(SDistPackage):
    origin = 'git'
    _version = 4

    @staticmethod
    def upgrade(config, version):
        # v2 adds support for multiple builders
        if version < 2:  # pragma: no branch
            config['builders'] = [config.pop('builder')]

        # v3 adds the `env` field.
        if version < 3:  # pragma: no branch
            config['env'] = {}

        # v4 moves `submodules.required` to `submodule_required` and stores
        # `submodules` as a dict of submodule names.
        if version < 4:
            if config['submodules']:
                config['submodule_required'] = config['submodules']['required']
                config['submodules'] = {
                    i: {} for i in config['submodules']['names']
                }

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
        return os.path.normpath(os.path.join(self._base_srcdir(metadata),
                                             self.srcdir))

    def clean_pre(self, metadata, new_package, quiet=False):
        if not self._needs_clean(new_package):
            return False

        if not quiet:
            log.pkg_clean(self.name, 'sources')
        shutil.rmtree(self._base_srcdir(metadata), ignore_errors=True)
        return True

    def fetch(self, metadata, parent_config):
        path_values = self.path_values(metadata, with_builders=False)
        base_srcdir = self._base_srcdir(metadata)

        env = self._expr_symbols['env'].value(path_values)
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
