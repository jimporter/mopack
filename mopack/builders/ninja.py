from . import Builder
from .. import types
from ..environment import get_cmd
from ..freezedried import GenericFreezeDried
from ..log import LogFile
from ..path import pushd
from ..shell import ShellArguments

_known_install_types = ('prefix', 'exec-prefix', 'bindir', 'libdir',
                        'includedir')


@GenericFreezeDried.fields(rehydrate={'extra_args': ShellArguments})
class NinjaBuilder(Builder):
    type = 'ninja'
    _version = 1

    @staticmethod
    def upgrade(config, version):
        return config

    def __init__(self, pkg, *, extra_args=None, _symbols, **kwargs):
        super().__init__(pkg, **kwargs)

        _symbols = _symbols.augment_path_bases(*self.path_bases())
        T = types.TypeCheck(locals(), _symbols)
        T.extra_args(types.shell_args(none_ok=True))

    def path_bases(self):
        return ()

    def path_values(self, metadata):
        return {}

    def build(self, metadata, pkg):
        path_values = pkg.path_values(metadata)

        env = self._common_options.env
        ninja = get_cmd(env, 'NINJA', 'ninja')
        with LogFile.open(metadata.pkgdir, self.name) as logfile:
            with pushd(path_values['builddir']):
                logfile.check_call(ninja, env=env)

    def deploy(self, metadata, pkg):
        path_values = pkg.path_values(metadata)

        env = self._common_options.env
        ninja = get_cmd(env, 'NINJA', 'ninja')
        with LogFile.open(metadata.pkgdir, self.name,
                          kind='deploy') as logfile:
            with pushd(path_values['builddir']):
                logfile.check_call(ninja + ['install'], env=env)
