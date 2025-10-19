import os

from . import ConfiguringBuilder, BuilderOptions
from .ninja import NinjaBuilder
from .. import types
from ..environment import get_cmd
from ..freezedried import GenericFreezeDried
from ..log import LogFile
from ..path import Path, pushd
from ..shell import ShellArguments

_known_install_types = ('prefix', 'exec-prefix', 'bindir', 'libdir',
                        'includedir')


@GenericFreezeDried.fields(rehydrate={'extra_args': ShellArguments})
class Bfg9000Builder(ConfiguringBuilder):
    type = 'bfg9000'
    _version = 4

    class Options(BuilderOptions):
        type = 'bfg9000'
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
        # v2 removes the `name` field.
        if version < 2:  # pragma: no branch
            del config['name']

        # v3 adds `directory`.
        if version < 3:  # pragma: no branch
            config['directory'] = Path('', 'srcdir').dehydrate()

        # v4 adds the `env` field.
        if version < 4:  # pragma: no branch
            config['env'] = {}

        return config

    def __init__(self, pkg, *, extra_args=None, _symbols, **kwargs):
        super().__init__(pkg, _symbols=_symbols, _child_builder=NinjaBuilder,
                         **kwargs)

        _symbols = _symbols.augment(path_bases=self.path_bases())
        T = types.TypeCheck(locals(), _symbols)
        T.extra_args(types.shell_args(none_ok=True))

    def filter_linkage(self, linkage):
        if linkage is None:
            return 'pkg_config'
        return linkage

    def _toolchain_args(self, toolchain):
        return ['--toolchain', toolchain] if toolchain else []

    def _install_args(self, deploy_dirs):
        args = []
        for k, v in deploy_dirs.items():
            if k in _known_install_types:
                args.extend(['--' + k, v])
        return args

    def build(self, metadata, pkg):
        path_values = pkg.path_values(metadata)

        env = self._full_env.value(path_values)
        bfg9000 = get_cmd(env, 'BFG9000', 'bfg9000')
        with LogFile.open(metadata.pkgdir, self.name) as logfile:
            with pushd(self.directory.string(path_values)):
                logfile.check_call(
                    bfg9000 + ['configure', path_values['builddir']] +
                    self._toolchain_args(self._this_options.toolchain) +
                    self._install_args(self._common_options.deploy_dirs) +
                    self.extra_args.args(path_values),
                    env=env
                )
        super().build(metadata, pkg)
