import os
import shutil

from . import Builder
from ..log import check_call_log, open_log
from ..path import pushd


class Bfg9000Builder(Builder):
    type = 'bfg9000'

    def __init__(self, name, *, builddir=None, extra_args=None):
        super().__init__(name)
        self.builddir = builddir or name
        self.extra_args = extra_args or []

    def _builddir(self, pkgdir):
        return os.path.abspath(os.path.join(pkgdir, 'build', self.builddir))

    def clean(self, pkgdir):
        shutil.rmtree(self._builddir(pkgdir), ignore_errors=True)

    def build(self, pkgdir, srcdir):
        builddir = self._builddir(pkgdir)

        with open_log(pkgdir, self.name) as log:
            with pushd(srcdir):
                check_call_log(['9k', builddir] + self.extra_args, log=log)
            with pushd(builddir):
                check_call_log(['ninja'], log=log)
        return os.path.abspath(builddir)
