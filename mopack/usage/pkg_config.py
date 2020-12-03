import os

from . import Usage
from .. import types
from ..iterutils import listify
from ..package_defaults import DefaultResolver


def _submodule_map(field, value):
    try:
        value = {'*': {'pcfile': types.string(field, value)}}
    except types.FieldError:
        pass

    return types.dict_of(
        types.string,
        types.dict_shape({
            'pcfile': types.string,
        }, 'a submodule map')
    )(field, value)


class PkgConfigUsage(Usage):
    type = 'pkg-config'

    def __init__(self, name, *, path='pkgconfig', pcfile=types.Unset,
                 extra_args=None, submodule_map=types.Unset, submodules,
                 symbols):
        package_default = DefaultResolver(self, symbols, name)

        self.path = types.abs_or_inner_path('path', path)
        if submodules and submodules['required']:
            # If submodules are required, default to an empty .pc file, since
            # we should usually have .pc files for the submodules that handle
            # everything for us.
            default_pcfile = None
        else:
            default_pcfile = name
        self.pcfile = types.default(types.string, default_pcfile)(
            'pcfile', pcfile
        )

        self.extra_args = types.shell_args()('extra_args', extra_args)

        if submodules:
            self.submodule_map = package_default(
                types.maybe(_submodule_map), default=name + '_{submodule}'
            )('submodule_map', submodule_map)

    def _get_submodule_mapping(self, submodule):
        if self.submodule_map is None:
            return {}
        try:
            return self.submodule_map[submodule]
        except KeyError:
            return {k: v.format(submodule=submodule)
                    for k, v in self.submodule_map['*'].items()}

    def get_usage(self, submodules, srcdir, builddir):
        base = builddir if builddir is not None else srcdir
        if base is None and not os.path.isabs(self.path):
            # XXX: It would probably be better to do this during construction.
            raise ValueError('`pkg-config` path must be absolute with ' +
                             'this package type')

        path = os.path.abspath(os.path.join(base, self.path))

        pcfiles = listify(self.pcfile)
        for i in submodules or []:
            f = self._get_submodule_mapping(i).get('pcfile')
            if f:
                pcfiles.append(f)

        return self._usage(path=path, pcfiles=pcfiles,
                           extra_args=self.extra_args)
