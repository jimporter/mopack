import os
import shutil
import warnings

from . import DirectoryBuilder
from .. import types
from ..freezedried import GenericFreezeDried, ListFreezeDryer
from ..log import LogFile
from ..path import Path, pushd
from ..shell import ShellArguments

_known_install_types = ('prefix', 'exec-prefix', 'bindir', 'libdir',
                        'includedir')

CommandsFD = ListFreezeDryer(ShellArguments)
_cmds_type = types.maybe(types.list_of(types.shell_args()), default=[])


@GenericFreezeDried.fields(rehydrate={'build_commands': CommandsFD,
                                      'deploy_commands': CommandsFD})
class CustomBuilder(DirectoryBuilder):
    type = 'custom'
    _version = 5

    @staticmethod
    def upgrade(config, version):
        # v2 removes the `name` field.
        if version < 2:  # pragma: no branch
            del config['name']

        # v3 adds `directory`.
        if version < 3:  # pragma: no branch
            config['directory'] = Path('', 'srcdir').dehydrate()

        # v4 adds `outdir`.
        if version < 4:  # pragma: no branch
            config['outdir'] = 'build'

        # v5 adds the `env` field.
        if version < 5:  # pragma: no branch
            config['env'] = {}

        return config

    def __init__(self, pkg, *, build_commands, deploy_commands=None,
                 directory=None, outdir=types.Unset, _symbols, **kwargs):
        # TODO: Remove this after v0.2 is released.
        if outdir is types.Unset:
            warnings.warn(types.FieldKeyWarning(
                ('`outdir` unspecified, defaulting to `build`; ' +
                 'this will default to `null` in a future release'),
                None
            ))
            outdir = 'build'

        if directory is None and _symbols.path_bases:
            directory = '$' + _symbols.path_bases[-1]

        T = types.TypeCheck(locals(), _symbols)
        T.outdir(types.maybe(types.symbol_name))
        _symbols = _symbols.augment(path_bases=self.path_bases())

        super().__init__(pkg, directory=directory, _symbols=_symbols, **kwargs)

        T = types.TypeCheck(locals(), _symbols)
        T.build_commands(_cmds_type)
        T.deploy_commands(_cmds_type)

    def _execute(self, logfile, commands, path_values):
        env = self._full_env.value(path_values)
        for line in commands:
            line = line.args(path_values)
            if line[0] == 'cd':
                with logfile.synthetic_command(line):
                    if len(line) != 2:
                        raise RuntimeError('invalid command format')
                    os.chdir(line[1])
            else:
                logfile.check_call(line, env=env)

    def path_bases(self):
        if self.outdir:
            return (self.outdir + 'dir',)
        return ()

    def path_values(self, metadata, parent_values):
        if self.outdir:
            outdir = os.path.abspath(os.path.join(metadata.pkgdir, self.outdir,
                                                  self.name))
            return {self.outdir + 'dir': outdir}
        return {}

    def clean(self, metadata, pkg):
        if self.outdir:
            path_values = pkg.path_values(metadata)
            shutil.rmtree(path_values['builddir'], ignore_errors=True)

    def build(self, metadata, pkg):
        path_values = pkg.path_values(metadata)

        with LogFile.open(metadata.pkgdir, self.name) as logfile:
            with pushd(self.directory.string(path_values), makedirs=True,
                       exist_ok=True):
                self._execute(logfile, self.build_commands, path_values)

    def deploy(self, metadata, pkg):
        path_values = pkg.path_values(metadata)

        directory = (path_values[self.outdir + 'dir'] if self.outdir else
                     self.directory.string(path_values))
        with LogFile.open(metadata.pkgdir, self.name,
                          kind='deploy') as logfile:
            with pushd(directory, makedirs=True, exist_ok=True):
                self._execute(logfile, self.deploy_commands, path_values)
