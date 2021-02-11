import os.path

from . import Builder, BuilderOptions
from .. import types
from ..environment import get_cmd
from ..freezedried import FreezeDried
from ..log import LogFile
from ..path import pushd
from ..shell import ShellArguments

# XXX: Handle exec-prefix, which CMake doesn't work with directly.
_known_install_types = ('prefix', 'bindir', 'libdir', 'includedir')


@FreezeDried.fields(rehydrate={'extra_args': ShellArguments})
class CMakeBuilder(Builder):
    type = 'cmake'
    _version = 1
    _path_bases = ('srcdir', 'builddir')

    class Options(BuilderOptions):
        type = 'cmake'
        _version = 1

        @staticmethod
        def upgrade(config, version):
            return config

        def __init__(self):
            self.toolchain = types.Unset

        def __call__(self, *, toolchain=types.Unset, config_file,
                     _symbols, _child_config=False):
            if not _child_config and self.toolchain is types.Unset:
                T = types.TypeCheck(locals(), _symbols)
                config_dir = os.path.dirname(config_file)
                T.toolchain(types.maybe_raw(types.path_string(config_dir)))

    @staticmethod
    def upgrade(config, version):
        return config

    def __init__(self, name, *, extra_args=None, submodules, **kwargs):
        super().__init__(name, **kwargs)

        T = types.TypeCheck(locals(), self._expr_symbols)
        T.extra_args(types.shell_args(none_ok=True))

    def _toolchain_args(self, toolchain):
        return ['-DCMAKE_TOOLCHAIN_FILE=' + toolchain] if toolchain else []

    def _install_args(self, deploy_paths):
        args = []
        for k, v in deploy_paths.items():
            if k in _known_install_types:
                args.append('-DCMAKE_INSTALL_{}:PATH={}'
                            .format(k.upper(), os.path.abspath(v)))
        return args

    def build(self, pkgdir, srcdir):
        builddir = self._builddir(pkgdir)

        cmake = get_cmd(self._common_options.env, 'CMAKE', 'cmake')
        ninja = get_cmd(self._common_options.env, 'NINJA', 'ninja')
        with LogFile.open(pkgdir, self.name) as logfile:
            with pushd(builddir, makedirs=True, exist_ok=True):
                logfile.check_call(
                    cmake + [srcdir, '-G', 'Ninja'] +
                    self._toolchain_args(self._this_options.toolchain) +
                    self._install_args(self._common_options.deploy_paths) +
                    self.extra_args.fill(srcdir=srcdir, builddir=builddir)
                )
                logfile.check_call(ninja)

    def deploy(self, pkgdir, srcdir):
        ninja = get_cmd(self._common_options.env, 'NINJA', 'ninja')
        with LogFile.open(pkgdir, self.name, kind='deploy') as logfile:
            with pushd(self._builddir(pkgdir)):
                logfile.check_call(ninja + ['install'])
