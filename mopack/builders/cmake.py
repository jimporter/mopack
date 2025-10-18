import os.path

from . import ConfiguringBuilder, BuilderOptions
from .ninja import NinjaBuilder
from .. import types
from ..environment import get_cmd
from ..freezedried import GenericFreezeDried
from ..log import LogFile
from ..path import Path, pushd
from ..shell import ShellArguments

# XXX: Handle exec-prefix, which CMake doesn't work with directly.
_known_install_types = ('prefix', 'bindir', 'libdir', 'includedir')


@GenericFreezeDried.fields(rehydrate={'extra_args': ShellArguments})
class CMakeBuilder(ConfiguringBuilder):
    type = 'cmake'
    _version = 3

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
        # v2 removes the name field.
        if version < 2:  # pragma: no branch
            del config['name']

        # v3 adds `directory`.
        if version < 3:  # pragma: no branch
            config['directory'] = Path('', 'srcdir').dehydrate()

        return config

    def __init__(self, pkg, *, extra_args=None, _symbols, **kwargs):
        super().__init__(pkg, _symbols=_symbols, _child_builder=NinjaBuilder,
                         **kwargs)

        _symbols = _symbols.augment(path_bases=self.path_bases())
        T = types.TypeCheck(locals(), _symbols)
        T.extra_args(types.shell_args(none_ok=True))

    def _toolchain_args(self, toolchain):
        return ['-DCMAKE_TOOLCHAIN_FILE=' + toolchain] if toolchain else []

    def _install_args(self, deploy_dirs):
        args = []
        for k, v in deploy_dirs.items():
            if k in _known_install_types:
                args.append('-DCMAKE_INSTALL_{}:PATH={}'
                            .format(k.upper(), os.path.abspath(v)))
        return args

    def build(self, metadata, pkg):
        path_values = pkg.path_values(metadata)

        env = self._common_options.env
        cmake = get_cmd(env, 'CMAKE', 'cmake')
        with LogFile.open(metadata.pkgdir, self.name) as logfile:
            with pushd(path_values['builddir'], makedirs=True, exist_ok=True):
                logfile.check_call(
                    cmake + [self.directory.string(**path_values),
                             '-G', 'Ninja'] +
                    self._toolchain_args(self._this_options.toolchain) +
                    self._install_args(self._common_options.deploy_dirs) +
                    self.extra_args.fill(**path_values),
                    env=env
                )
        super().build(metadata, pkg)
