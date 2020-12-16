import os.path

from . import Builder
from .. import types
from ..log import LogFile
from ..path import pushd
from ..shell import get_cmd

# XXX: Handle exec-prefix, which CMake doesn't work with directly.
_known_install_types = ('prefix', 'bindir', 'libdir', 'includedir')


class CMakeBuilder(Builder):
    type = 'cmake'
    _path_bases = ('srcdir', 'builddir')

    def __init__(self, name, *, extra_args=None, submodules, **kwargs):
        super().__init__(name, **kwargs)
        self.extra_args = types.maybe(types.shell_args(self._path_bases), [])(
            'extra_args', extra_args
        )

    def _install_args(self, deploy_paths):
        args = []
        for k, v in deploy_paths.items():
            if k in _known_install_types:
                args.append('-DCMAKE_INSTALL_{}:PATH={}'
                            .format(k.upper(), os.path.abspath(v)))
        return args

    def build(self, pkgdir, srcdir, deploy_paths={}):
        builddir = self._builddir(pkgdir)

        cmake = get_cmd(self._common_options.env, 'CMAKE', 'cmake')
        ninja = get_cmd(self._common_options.env, 'NINJA', 'ninja')
        with LogFile.open(pkgdir, self.name) as logfile:
            with pushd(builddir, makedirs=True, exist_ok=True):
                logfile.check_call(
                    cmake + [srcdir, '-G', 'Ninja'] +
                    self._install_args(deploy_paths) +
                    self.extra_args
                )
                logfile.check_call(ninja)

    def deploy(self, pkgdir):
        ninja = get_cmd(self._common_options.env, 'NINJA', 'ninja')
        with LogFile.open(pkgdir, self.name, kind='deploy') as logfile:
            with pushd(self._builddir(pkgdir)):
                logfile.check_call(ninja + ['install'])
