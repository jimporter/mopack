import os

from .library import LibraryUsage
from .. import types

_list_of_paths = types.list_of(types.inner_path, listify=True)


class PathUsage(LibraryUsage):
    type = 'path'

    def __init__(self, name, *, include_path=None, library_path=None,
                 **kwargs):
        super().__init__(name, **kwargs)
        self.include_path = _list_of_paths('include_path', include_path)
        self.library_path = _list_of_paths('library_path', library_path)

    def get_usage(self, submodules, srcdir, builddir):
        if srcdir is None or builddir is None:
            # XXX: It would probably be better to do this during construction.
            raise ValueError('unable to use `path` usage with this package ' +
                             'type; try `system` usage')

        # XXX: Provide a way of specifying what these paths are relative to
        # instead of just assuming that includes are in the srcdir and libs are
        # in the builddir.
        return self._usage(
            include_path=[os.path.abspath(os.path.join(srcdir, i))
                          for i in self.include_path],
            library_path=[os.path.abspath(os.path.join(builddir, i))
                          for i in self.library_path],
            libraries=self._get_libraries(submodules),
        )
