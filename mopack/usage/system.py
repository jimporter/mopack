from . import Usage


class SystemUsage(Usage):
    type = 'system'

    def usage(self, srcdir, builddir):
        return self._usage()
