import os

from ..log import check_call_log, open_log
from ..path import pushd


class Bfg9000Builder:
    def __init__(self, name, builddir='build'):
        self.name = name
        self.builddir = builddir

    def build(self, pkgdir, srcdir):
        # FIXME: This puts the builddir in the wrong spot for `directory`
        # sources.
        builddir = os.path.join(srcdir, self.builddir)

        with open_log(pkgdir, self.name) as log:
            with pushd(srcdir):
                check_call_log(['9k', self.builddir, '--debug'], log=log)
            with pushd(builddir):
                check_call_log(['ninja'], log=log)
        return os.path.abspath(builddir)
