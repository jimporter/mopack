from itertools import chain

from . import Usage
from .. import types
from ..iterutils import iterate
from ..package_defaults import package_default
from ..platforms import package_library_name

__all__ = ['LibraryUsage', 'list_of_libraries']


def _library(field, value):
    value = types.dict_shape({
        'type': types.constant('library', 'guess', 'framework'),
        'name': types.string
    }, desc='library')(field, value)
    if value['type'] == 'library':
        return value['name']
    return value


list_of_libraries = types.list_of(types.one_of(
    types.string, _library, desc='library'
), listify=True)


class LibraryUsage(Usage):
    _skip_fields = Usage._skip_fields + ('general_options',)

    def __init__(self, name, *, libraries=types.Unset,
                 submodule_map=types.Unset, submodules):
        if submodules and submodules['required']:
            # If submodules are required, default to an empty list of
            # libraries, since we likely don't have a "base" library that
            # always needs linking to.
            libs_checker = types.default(list_of_libraries, [])
        else:
            libs_checker = package_default(list_of_libraries, name, default={
                'type': 'guess', 'name': name
            })
        self.libraries = libs_checker('libraries', libraries)

        if submodules:
            self.submodule_map = types.default(
                types.maybe(types.string), '{package}_{submodule}'
            )('submodule_map', submodule_map)
            if self.submodule_map is not None:
                self.submodule_map = self.submodule_map.format(
                    package=name, submodule='{submodule}'
                )

    def _get_libraries(self, submodules):
        def make_library(lib):
            if isinstance(lib, dict) and lib.get('type') == 'guess':
                return package_library_name(
                    self.general_options.target_platform or None, lib['name']
                )
            return lib

        if submodules and self.submodule_map:
            libraries = chain( self.libraries,
                               (self.submodule_map.format(submodule=i)
                                for i in iterate(submodules)) )
        else:
            libraries = self.libraries
        return [make_library(i) for i in libraries]

    def set_options(self, options):
        self.general_options = options['general']
