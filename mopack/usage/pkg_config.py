from . import submodule_placeholder, Usage
from .. import types
from ..freezedried import DictFreezeDryer, FreezeDried
from ..iterutils import listify
from ..package_defaults import DefaultResolver
from ..path import Path
from ..placeholder import placeholder, PlaceholderFD
from ..shell import ShellArguments

_SubmoduleFD = PlaceholderFD(submodule_placeholder)


@FreezeDried.fields(rehydrate={'pcfile': _SubmoduleFD})
class _SubmoduleMapping(FreezeDried):
    def __init__(self, *, pcfile=None):
        def P(other):
            return types.placeholder_check(other, submodule_placeholder)

        T = types.TypeCheck(locals())
        T.pcfile(P(types.maybe(types.string)))

    def fill(self, submodule_name):
        def P(other):
            return types.placeholder_fill(other, submodule_placeholder,
                                          submodule_name)

        result = type(self).__new__(type(self))
        T = types.TypeCheck(self.__dict__, dest=result)
        T.pcfile(P(types.maybe(types.string)))
        return result


def _submodule_map(field, value):
    def check_item(field, value):
        with types.wrap_field_error(field):
            return _SubmoduleMapping(**value)

    try:
        value = {'*': {'pcfile': types.placeholder_string(field, value)}}
    except types.FieldError:
        pass

    return types.dict_of(types.string, check_item)(field, value)


@FreezeDried.fields(rehydrate={
    'path': Path, 'extra_args': ShellArguments,
    'submodule_map': DictFreezeDryer(value_type=_SubmoduleMapping),
})
class PkgConfigUsage(Usage):
    type = 'pkg_config'
    _version = 1

    @staticmethod
    def upgrade(config, version):
        return config

    def __init__(self, name, *, path='pkgconfig', pcfile=types.Unset,
                 extra_args=None, submodule_map=types.Unset, submodules,
                 _options, _path_bases):
        super().__init__(_options=_options)
        symbols = self._expr_symbols(_path_bases)
        package_default = DefaultResolver(self, symbols, name)
        buildbase = self._preferred_base('builddir', _path_bases)
        if submodules and submodules['required']:
            # If submodules are required, default to an empty .pc file, since
            # we should usually have .pc files for the submodules that handle
            # everything for us.
            default_pcfile = None
        else:
            default_pcfile = name

        T = types.TypeCheck(locals(), symbols)
        T.path(types.abs_or_inner_path(buildbase))
        T.pcfile(types.maybe(types.string, default=default_pcfile))
        T.extra_args(types.shell_args(none_ok=True))

        if submodules:
            submodule_var = placeholder(submodule_placeholder)
            extra_symbols = {'submodule': submodule_var}
            T.submodule_map(package_default(
                types.maybe(_submodule_map),
                default=name + '_' + submodule_var,
                extra_symbols=extra_symbols
            ), extra_symbols=extra_symbols)

    def _get_submodule_mapping(self, submodule):
        try:
            return self.submodule_map[submodule].fill(submodule)
        except KeyError:
            return self.submodule_map['*'].fill(submodule)

    def get_usage(self, submodules, srcdir, builddir):
        pcpath = self.path.string(srcdir=srcdir, builddir=builddir)
        extra_args = self.extra_args.fill(srcdir=srcdir, builddir=builddir)

        if submodules and self.submodule_map:
            mappings = [self._get_submodule_mapping(i) for i in submodules]
        else:
            mappings = []

        pcfiles = listify(self.pcfile)
        for i in mappings:
            if i.pcfile:
                pcfiles.append(i.pcfile)

        return self._usage(path=pcpath, pcfiles=pcfiles, extra_args=extra_args)
