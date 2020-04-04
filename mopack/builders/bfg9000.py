import os
import subprocess

from ..path import pushd


def check_call_log(args, log):
    subprocess.check_call(args, stdout=log, stderr=log)


class Bfg9000Builder:
    def __init__(self, name, srcdir=None, builddir='build'):
        self.name = name
        self.srcdir = srcdir
        self.builddir = builddir

    def build(self, pkgdir, guessed_srcdir):
        srcdir = self.srcdir or guessed_srcdir
        # FIXME: This puts the builddir in the wrong spot for `directory`
        # sources.
        builddir = os.path.join(srcdir, self.builddir)

        logname = os.path.join(pkgdir, '{}.log'.format(self.name))
        with open(logname, 'w') as log:
            with pushd(srcdir):
                check_call_log(['9k', self.builddir, '--debug'], log=log)
            with pushd(builddir):
                check_call_log(['ninja'], log=log)
        return os.path.abspath(builddir)
