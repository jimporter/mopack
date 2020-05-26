import os

from . import Usage
from .. import types
from ..iterutils import iterate, listify
from ..package_defaults import package_default


class PkgConfigUsage(Usage):
    type = 'pkg-config'

    def __init__(self, name, *, path='pkgconfig', pcfile=types.Unset,
                 submodule_map=types.Unset, submodules):
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

        if submodules:
            self.submodule_map = package_default(
                types.maybe(types.string), name,
                field='pkg_config_submodule_map',
                default='{package}_{submodule}'
            )('submodule_map', submodule_map)
            if self.submodule_map is not None:
                self.submodule_map = self.submodule_map.format(
                    package=name, submodule='{submodule}'
                )

    def get_usage(self, submodules, srcdir, builddir):
        if builddir is None:
            # XXX: It would probably be better to do this during construction.
            raise ValueError('unable to use `pkg-config` usage with ' +
                             'this package type; try `system` usage')

        path = os.path.abspath(os.path.join(builddir, self.path))

        pcfiles = listify(self.pcfile)
        if submodules and self.submodule_map:
            pcfiles.extend(self.submodule_map.format(submodule=i)
                           for i in iterate(submodules))
        return self._usage(path=path, pcfiles=pcfiles)
