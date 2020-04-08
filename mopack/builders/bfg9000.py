import os

from ..log import check_call_log, open_log
from ..path import pushd


class Bfg9000Builder:
    def __init__(self, name, builddir=None):
        self.name = name
        self.builddir = builddir or name

    def build(self, pkgdir, srcdir):
        builddir = os.path.abspath(os.path.join(
            pkgdir, 'build', self.builddir
        ))

        with open_log(pkgdir, self.name) as log:
            with pushd(srcdir):
                check_call_log(['9k', builddir, '--debug'], log=log)
            with pushd(builddir):
                check_call_log(['ninja'], log=log)
        return os.path.abspath(builddir)
