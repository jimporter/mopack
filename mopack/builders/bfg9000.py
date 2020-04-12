import os
import shutil

from . import Builder
from ..log import check_call_log, open_log
from ..path import pushd

_known_install_types = ('prefix', 'exec-prefix', 'bindir', 'libdir',
                        'includedir')


class Bfg9000Builder(Builder):
    type = 'bfg9000'

    def __init__(self, name, *, builddir=None, extra_args=None):
        super().__init__(name)
        self.builddir = builddir or name
        self.extra_args = extra_args or []

    def _builddir(self, pkgdir):
        return os.path.abspath(os.path.join(pkgdir, 'build', self.builddir))

    def _install_args(self, deploy_paths):
        args = []
        for k, v in deploy_paths.items():
            if k in _known_install_types:
                args.extend(['--' + k, v])
        return args

    def clean(self, pkgdir):
        shutil.rmtree(self._builddir(pkgdir), ignore_errors=True)

    def build(self, pkgdir, srcdir, deploy_paths={}):
        builddir = self._builddir(pkgdir)

        with open_log(pkgdir, self.name) as log:
            with pushd(srcdir):
                args = (['9k', builddir] + self._install_args(deploy_paths) +
                        self.extra_args)
                check_call_log(args, log=log)
            with pushd(builddir):
                check_call_log(['ninja'], log=log)
        return os.path.abspath(builddir)

    def deploy(self, pkgdir):
        with open_log(pkgdir, self.name + '-deploy') as log:
            with pushd(self._builddir(pkgdir)):
                check_call_log(['ninja', 'install'], log=log)
