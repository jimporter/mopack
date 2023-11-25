import subprocess
from collections import ChainMap

from . import Linkage
from . import submodules as submod
from .. import types
from ..environment import get_pkg_config, subprocess_run
from ..freezedried import (DictFreezeDryer, FreezeDried, GenericFreezeDried,
                           ListFreezeDryer)
from ..iterutils import listify
from ..package_defaults import DefaultResolver
from ..path import Path
from ..shell import join_paths


class _SubmoduleMapping(FreezeDried):
    def __init__(self, symbols, *, pcname=None):
        # Since we need to delay evaluating symbols until we know what the
        # selected submodule is, just store these values unevaluated. We'll
        # evaluate them later during `mopack linkage` via the fill() function.
        self.pcname = pcname

        # Just check that we can fill submodule values correctly.
        self.fill(symbols, 'SUBMODULE')

    def fill(self, symbols, submodule_name):
        def P(other):
            return types.placeholder_fill(other, submod.placeholder,
                                          submodule_name)

        symbols = symbols.augment_symbols(**submod.expr_symbols)

        result = type(self).__new__(type(self))
        T = types.TypeCheck(self.__dict__, symbols, dest=result)
        T.pcname(P(types.maybe(types.string)))
        return result


def _submodule_map(symbols):
    def check_item(field, value):
        with types.wrap_field_error(field):
            return _SubmoduleMapping(symbols, **value)

    def check(field, value):
        try:
            value = {'*': {'pcname': types.placeholder_string(field, value)}}
        except types.FieldError:
            pass

        return types.dict_of(types.string, check_item)(field, value)

    return check


@GenericFreezeDried.fields(rehydrate={
    'pkg_config_path': ListFreezeDryer(Path),
    'submodule_map': DictFreezeDryer(value_type=_SubmoduleMapping),
})
class PkgConfigLinkage(Linkage):
    type = 'pkg_config'
    _version = 1

    @staticmethod
    def upgrade(config, version):
        return config

    def __init__(self, pkg, *, pcname=types.Unset, pkg_config_path='pkgconfig',
                 submodule_map=types.Unset, inherit_defaults=False, **kwargs):
        super().__init__(pkg, inherit_defaults=inherit_defaults, **kwargs)

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
            T.submodule_map(pkg_default(
                types.maybe(_submodule_map(symbols)),
                default=pkg.name + '_$submodule',
                extra_symbols=submod.expr_symbols,
                evaluate=False
            ), evaluate=False)

    def version(self, metadata, pkg):
        pkg_config = get_pkg_config(self._common_options.env)
        path_values = pkg.path_values(metadata)
        pkgconfpath = [i.string(**path_values) for i in self.pkg_config_path]
        env = ChainMap({'PKG_CONFIG_PATH': join_paths(pkgconfpath)},
                       self._common_options.env)

        return subprocess_run(
            pkg_config + [self.pcname, '--modversion'], check=True,
            stdout=subprocess.PIPE, universal_newlines=True, env=env
        ).stdout.strip()

    def _get_submodule_mapping(self, symbols, submodule):
        try:
            mapping = self.submodule_map[submodule]
        except KeyError:
            mapping = self.submodule_map['*']
        return mapping.fill(symbols, submodule)

    def get_linkage(self, metadata, pkg, submodules):
        path_values = pkg.path_values(metadata)
        pkgconfpath = [i.string(**path_values) for i in self.pkg_config_path]

        if submodules and self.submodule_map:
            mappings = [self._get_submodule_mapping(self._expr_symbols, i)
                        for i in submodules]
        else:
            mappings = []

        pcnames = listify(self.pcname)
        for i in mappings:
            if i.pcname:
                pcnames.append(i.pcname)

        return self._linkage(submodules, pcnames=pcnames,
                             pkg_config_path=pkgconfpath)
