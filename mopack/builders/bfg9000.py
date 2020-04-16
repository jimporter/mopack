import os
import shutil

from . import Builder
from .. import types
from ..log import LogFile
from ..path import pushd
from ..usage import Usage, make_usage

_known_install_types = ('prefix', 'exec-prefix', 'bindir', 'libdir',
                        'includedir')


class Bfg9000Builder(Builder):
    type = 'bfg9000'
    _rehydrate_fields = {'usage': Usage}

    def __init__(self, name, *, extra_args=None, usage=None):
        super().__init__(name)
        self.extra_args = types.shell_args('extra_args', extra_args)
        self.usage = make_usage(usage or 'pkgconfig')

    def _builddir(self, pkgdir):
        return os.path.abspath(os.path.join(pkgdir, 'build', self.name))

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

        with LogFile.open(pkgdir, self.name) as logfile:
            with pushd(srcdir):
                logfile.check_call(['9k', builddir] +
                                   self._install_args(deploy_paths) +
                                   self.extra_args)
            with pushd(builddir):
                logfile.check_call(['ninja'])
        return self.usage.usage(os.path.abspath(builddir))

    def deploy(self, pkgdir):
        with LogFile.open(pkgdir, self.name + '-deploy') as logfile:
            with pushd(self._builddir(pkgdir)):
                logfile.check_call(['ninja', 'install'])
