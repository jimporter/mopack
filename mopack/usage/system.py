from .library import LibraryUsage
from .. import types
from ..package_defaults import package_default

list_of_headers = types.list_of(types.string, listify=True)


class SystemUsage(LibraryUsage):
    type = 'system'

    def __init__(self, name, *, headers=types.Unset, **kwargs):
        super().__init__(name, **kwargs)
        self.headers = package_default(list_of_headers, name)(
            'headers', headers
        )

    def get_usage(self, submodules, srcdir, builddir):
        return self._usage(
            headers=self.headers,
            libraries=self._get_libraries(submodules),
        )
