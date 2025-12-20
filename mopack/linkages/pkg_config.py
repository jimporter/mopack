import subprocess
from collections import ChainMap
from typing import List

from . import Linkage
from . import submodules as submod
from .. import types
from ..environment import get_pkg_config, subprocess_run
from ..freezedried import FreezeDried, GenericFreezeDried
from ..iterutils import listify
from ..package_defaults import DefaultResolver
from ..path import Path
from ..shell import join_paths
from ..objutils import Unset


@GenericFreezeDried.fields(include={'_if'})
class _SubmoduleLinkage(FreezeDried):
    def __init__(self, symbols, *, _if=True, pcname=None):
        self._if = _if
        # Since we need to delay evaluating symbols until we know what the
        # selected submodule is, just store these values unevaluated. We'll
        # evaluate them later during `mopack linkage` via the fill() function.
        self.pcname = pcname

        # Just check that we can fill submodule values correctly.
        self.fill(symbols, 'SUBMODULE')

    def evaluate_if(self, symbols, submodule_name):
        return submod.evaluate_if(symbols, self._if, submodule_name)

    def fill(self, symbols, submodule_name):
        def P(other):
            return types.placeholder_fill(other, submod.placeholder,
                                          submodule_name)

        symbols = symbols.augment(symbols=submod.expr_symbols)

        result = type(self).__new__(type(self))
        T = types.TypeCheck(vars(self), symbols, dest=result)
        T.pcname(P(types.maybe(types.string)))
        return result


def _submodule_linkage(symbols):
    def check_item(field, value):
        with types.wrap_field_error(field):
            return _SubmoduleLinkage(symbols, **types.mangle_keywords(value))

    def check(field, value):
        try:
            value = {'pcname': types.placeholder_string(field, value)}
        except types.FieldError:
            pass

        return types.list_of(check_item, listify=True)(field, value)

    return check


@GenericFreezeDried.fields(rehydrate={
    'pkg_config_path': List[Path],
    'submodule_linkage': List[_SubmoduleLinkage],
})
class PkgConfigLinkage(Linkage):
    type = 'pkg_config'
    _version = 2

    @staticmethod
    def upgrade(config, version):
        # v2 replaces `submodule_map` with `submodule_linkage`.
        if version < 2:  # pragma: no branch
            config['submodule_linkage'] = submod.migrate_saved_submodule_map(
                config.pop('submodule_map', None)
            )

        return config

    # TODO: Remove `submodule_map` after v0.2 is released.
    def __init__(self, pkg, *, pcname=Unset, pkg_config_path='pkgconfig',
                 submodule_linkage=Unset, submodule_map=Unset,
                 inherit_defaults=False, **kwargs):
        super().__init__(pkg, inherit_defaults=inherit_defaults, **kwargs)
        if submodule_linkage is Unset and submodule_map is not Unset:
            submodule_linkage = submod.migrate_submodule_map(submodule_map)

        symbols = self._expr_symbols
        pkg_default = DefaultResolver(self, symbols, inherit_defaults,
                                      pkg.name)
        buildbase = symbols.best_path_base('builddir')
        if pkg.submodules and pkg.submodules['required']:
            # If submodules are required, default to an empty .pc file, since
            # we should usually have .pc files for the submodules that handle
            # everything for us.
            default_pcname = None
        else:
            default_pcname = pkg.name

        T = types.TypeCheck(locals(), symbols)
        T.pcname(types.maybe(types.string, default=default_pcname))
        T.pkg_config_path(types.list_of(types.abs_or_inner_path(buildbase),
                                        listify=True))

        if pkg.submodules:
            T.submodule_linkage(pkg_default(
                types.maybe(_submodule_linkage(symbols)),
                default=pkg.name + '_$submodule',
                extra_symbols=submod.expr_symbols,
                evaluate=False
            ), evaluate=False)

    def version(self, metadata, pkg):
        pkg_config = get_pkg_config(self._common_options.env)
        path_values = pkg.path_values(metadata)
        pkgconfpath = [i.string(path_values) for i in self.pkg_config_path]
        env = ChainMap({'PKG_CONFIG_PATH': join_paths(pkgconfpath)},
                       self._common_options.env)

        return subprocess_run(
            pkg_config + [self.pcname, '--modversion'], check=True,
            stdout=subprocess.PIPE, universal_newlines=True, env=env
        ).stdout.strip()

    def _get_submodule_linkage(self, symbols, submodule):
        for i in self.submodule_linkage:
            if i.evaluate_if(symbols, submodule):
                return i.fill(symbols, submodule)
        raise ValueError('unable to get submodule linkage for {}'
                         .format(submodule))

    def get_linkage(self, metadata, pkg, submodules):
        path_values = pkg.path_values(metadata)
        pkgconfpath = [i.string(path_values) for i in self.pkg_config_path]

        if submodules and self.submodule_linkage:
            sublinks = [self._get_submodule_linkage(self._expr_symbols, i)
                        for i in submodules]
        else:
            sublinks = []

        pcnames = listify(self.pcname)
        for i in sublinks:
            if i.pcname:
                pcnames.append(i.pcname)

        return self._linkage(submodules, pcnames=pcnames,
                             pkg_config_path=pkgconfpath)
