from . import DirectoryBuilder
from .. import types
from ..environment import get_cmd
from ..freezedried import GenericFreezeDried
from ..log import LogFile
from ..path import pushd
from ..shell import ShellArguments

_known_install_types = ('prefix', 'exec-prefix', 'bindir', 'libdir',
                        'includedir')


@GenericFreezeDried.fields(rehydrate={'extra_args': ShellArguments})
class NinjaBuilder(DirectoryBuilder):
    type = 'ninja'
    _version = 2

    @staticmethod
    def upgrade(config, version):
        # v2 adds the `env` field.
        if version < 2:  # pragma: no branch
            config['env'] = {}

        return config

    def __init__(self, pkg, *, directory=None, extra_args=None, _symbols,
                 **kwargs):
        super().__init__(pkg, _symbols=_symbols, **kwargs)

        _symbols = _symbols.augment(path_bases=self.path_bases())
        if directory is None and _symbols.path_bases:
            directory = '$' + _symbols.path_bases[-1]
        T = types.TypeCheck(locals(), _symbols)
        T.extra_args(types.shell_args(none_ok=True))
        T.directory(types.any_path('cfgdir'))

    # TODO: Support clean here too?

    def build(self, metadata, pkg):
        path_values = pkg.path_values(metadata)

        env = self._full_env.value(path_values)
        ninja = get_cmd(env, 'NINJA', 'ninja')
        with LogFile.open(metadata.pkgdir, self.name) as logfile:
            with pushd(self.directory.string(path_values)):
                logfile.check_call(ninja, env=env)

    def deploy(self, metadata, pkg):
        path_values = pkg.path_values(metadata)

        env = self._full_env.value(path_values)
        ninja = get_cmd(env, 'NINJA', 'ninja')
        with LogFile.open(metadata.pkgdir, self.name,
                          kind='deploy') as logfile:
            with pushd(self.directory.string(path_values)):
                logfile.check_call(ninja + ['install'], env=env)
