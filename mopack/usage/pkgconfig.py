import os

from . import Usage
from .. import types


class PkgConfigUsage(Usage):
    type = 'pkgconfig'

    def __init__(self, *, path='pkgconfig'):
        self.path = types.inner_path('path', path, none_ok=False)

    def usage(self, builddir):
        if builddir is None:
            # XXX: It would probably be better to do this during construction.
            raise ValueError('unable to use `pkgconfig` usage with ' +
                             'this package type; try `system` usage')

        path = os.path.normpath(os.path.join(builddir, self.path))
        return self._usage(path=path)
