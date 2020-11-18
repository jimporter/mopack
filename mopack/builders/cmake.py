import os.path
import shutil

from . import Builder
from .. import types
from ..log import LogFile
from ..path import pushd

# XXX: Handle exec-prefix, which CMake doesn't work with directly.
_known_install_types = ('prefix', 'bindir', 'libdir', 'includedir')


class CMakeBuilder(Builder):
    type = 'cmake'

    def __init__(self, name, *, extra_args=None, usage, submodules=None,
                 **kwargs):
        super().__init__(name, usage=usage, **kwargs)
        self.extra_args = types.shell_args()('extra_args', extra_args)

    def _install_args(self, deploy_paths):
        args = []
        for k, v in deploy_paths.items():
            if k in _known_install_types:
                args.append('-DCMAKE_INSTALL_{}:PATH={}'
                            .format(k.upper(), os.path.abspath(v)))
        return args

    def clean(self, pkgdir):
        shutil.rmtree(self._builddir(pkgdir), ignore_errors=True)

    def build(self, pkgdir, srcdir, deploy_paths={}):
        builddir = self._builddir(pkgdir)

        with LogFile.open(pkgdir, self.name) as logfile:
            with pushd(builddir, makedirs=True, exist_ok=True):
                logfile.check_call(
                    ['cmake', srcdir, '-G', 'Ninja'] +
                    self._install_args(deploy_paths) +
                    self.extra_args
                )
                logfile.check_call(['ninja'])

    def deploy(self, pkgdir):
        with LogFile.open(pkgdir, self.name, kind='deploy') as logfile:
            with pushd(self._builddir(pkgdir)):
                logfile.check_call(['ninja', 'install'])
