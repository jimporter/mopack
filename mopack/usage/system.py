from . import Usage


class SystemUsage(Usage):
    type = 'system'

    def usage(self, builddir):
        return self._usage()
