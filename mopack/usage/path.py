import os

from . import Usage
from .. import types


class PathUsage(Usage):
    type = 'path'

    def __init__(self, *, include_path=None, library_path=None):
        self.include_path = types.maybe(types.inner_path)(
            'include_path', include_path
        )
        self.library_path = types.maybe(types.inner_path)(
            'library_path', library_path
        )

    def usage(self, srcdir, builddir):
        if srcdir is None or builddir is None:
            # XXX: It would probably be better to do this during construction.
            raise ValueError('unable to use `path` usage with this package ' +
                             'type; try `system` usage')

        # XXX: Provide a way of specifying what these paths are relative to
        # instead of just assuming that includes are in the srcdir and libs are
        # in the builddir.
        include_path = os.path.normpath(os.path.join(
            srcdir, self.include_path
        ))
        library_path = os.path.normpath(os.path.join(
            builddir, self.library_path
        ))
        return self._usage(include_path=include_path,
                           library_path=library_path)
