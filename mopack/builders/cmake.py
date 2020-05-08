import os
import shutil

from . import Builder
from .. import types
from ..log import LogFile
from ..path import pushd
from ..usage import Usage, make_usage

# XXX: Handle exec-prefix, which CMake doesn't work with directly.
_known_install_types = ('prefix', 'bindir', 'libdir', 'includedir')


class CMakeBuilder(Builder):
    type = 'cmake'
    _rehydrate_fields = {'usage': Usage}

    def __init__(self, name, *, extra_args=None, usage):
        super().__init__(name)
        self.extra_args = types.shell_args('extra_args', extra_args)
        self.usage = make_usage(usage)

    def _builddir(self, pkgdir):
        return os.path.abspath(os.path.join(pkgdir, 'build', self.name))

    def _install_args(self, deploy_paths):
        args = []
        for k, v in deploy_paths.items():
            if k in _known_install_types:
                args.append('-DCMAKE_INSTALL_{}:PATH={}'.format(k.upper(), v))
        return args

    def clean(self, pkgdir):
        shutil.rmtree(self._builddir(pkgdir), ignore_errors=True)

    def build(self, pkgdir, srcdir, deploy_paths={}):
        builddir = self._builddir(pkgdir)

        with LogFile.open(pkgdir, self.name) as logfile:
            with pushd(builddir, makedirs=True, exist_ok=True):
                logfile.check_call(
                    ['cmake', srcdir] +
                    self._install_args(deploy_paths) +
                    self.extra_args
                )
                logfile.check_call(['make'])
        return self.usage.usage(srcdir, builddir)

    def deploy(self, pkgdir):
        with LogFile.open(pkgdir, self.name + '-deploy') as logfile:
            with pushd(self._builddir(pkgdir)):
                logfile.check_call(['make', 'install'])
