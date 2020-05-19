from . import Usage
from .. import types
from ..platforms import package_library_name

__all__ = ['library_list', 'library_type', 'LibraryUsage']


def _library(field, value):
    value = types.dict_shape({
        'type': types.constant('library', 'guess', 'framework'),
        'name': types.string
    })(field, value)
    if value['type'] == 'library':
        return value['name']
    return value


library_type = types.list_of(types.one_of(
    types.string, _library, desc='library'
))


def library_list(package_name):
    def check(field, value):
        if value is types.Unset:
            value = {'type': 'guess', 'name': package_name}
        return library_type(field, value)

    return check


class LibraryUsage(Usage):
    _skip_fields = Usage._skip_fields + ('general_options',)

    def __init__(self, name, *, libraries=types.Unset):
        self.libraries = library_list(name)('libraries', libraries)

    def _make_library(self, library):
        if isinstance(library, dict) and library.get('type') == 'guess':
            return package_library_name(
                self.general_options.target_platform or None, library['name']
            )
        return library

    def set_options(self, options):
        self.general_options = options['general']
