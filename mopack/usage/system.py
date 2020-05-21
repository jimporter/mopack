from .library import LibraryUsage
from .. import types


class SystemUsage(LibraryUsage):
    type = 'system'

    def __init__(self, name, *, headers=None, **kwargs):
        super().__init__(name, **kwargs)
        self.headers = types.list_of(types.string, listify=True)(
            'headers', headers
        )

    def get_usage(self, srcdir, builddir):
        return self._usage(
            headers=self.headers,
            libraries=[self._make_library(i) for i in self.libraries],
        )
