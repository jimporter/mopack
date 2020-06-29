import os

from . import Usage
from .. import types
from ..iterutils import listify


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
                 extra_args=None, submodule_map=types.Unset, submodules):
        self.path = types.inner_path('path', path)
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
            self.submodule_map = self._package_default(
                types.maybe(_submodule_map), name,
                default=name + '_{submodule}'
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
        if builddir is None:
            # XXX: It would probably be better to do this during construction.
            raise ValueError('unable to use `pkg-config` usage with ' +
                             'this package type; try `system` usage')

        path = os.path.abspath(os.path.join(builddir, self.path))

        pcfiles = listify(self.pcfile)
        for i in submodules or []:
            f = self._get_submodule_mapping(i).get('pcfile')
            if f:
                pcfiles.append(f)

        return self._usage(path=path, pcfiles=pcfiles,
                           extra_args=self.extra_args)
