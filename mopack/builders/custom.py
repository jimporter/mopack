import os
import shutil

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
    _version = 3

    @staticmethod
    def upgrade(config, version):
        # v2 removes the `name` field.
        if version < 2:  # pragma: no branch
            del config['name']

        # v3 adds `directory`.
        if version < 3:  # pragma: no branch
            config['directory'] = Path('', Path.Base.srcdir).dehydrate()

        return config

    def __init__(self, pkg, *, build_commands, deploy_commands=None, _symbols,
                 **kwargs):
        super().__init__(pkg, _symbols=_symbols, **kwargs)

        _symbols = _symbols.augment_path_bases(*self.path_bases())
        T = types.TypeCheck(locals(), _symbols)
        T.build_commands(_cmds_type)
        T.deploy_commands(_cmds_type)

    def _execute(self, logfile, commands, path_values):
        for line in commands:
            line = line.fill(**path_values)
            if line[0] == 'cd':
                with logfile.synthetic_command(line):
                    if len(line) != 2:
                        raise RuntimeError('invalid command format')
                    os.chdir(line[1])
            else:
                logfile.check_call(line, env=self._common_options.env)

    def path_bases(self):
        return ('builddir',)

    def path_values(self, metadata):
        builddir = os.path.abspath(os.path.join(metadata.pkgdir, 'build',
                                                self.name))
        return {'builddir': builddir}

    def clean(self, metadata, pkg):
        path_values = pkg.path_values(metadata)
        shutil.rmtree(path_values['builddir'], ignore_errors=True)

    def build(self, metadata, pkg):
        path_values = pkg.path_values(metadata)

        with LogFile.open(metadata.pkgdir, self.name) as logfile:
            with pushd(self.directory.string(**path_values)):
                self._execute(logfile, self.build_commands, path_values)

    def deploy(self, metadata, pkg):
        path_values = pkg.path_values(metadata)

        with LogFile.open(metadata.pkgdir, self.name,
                          kind='deploy') as logfile:
            with pushd(path_values['builddir']):
                self._execute(logfile, self.deploy_commands, path_values)
