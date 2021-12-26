import os

from . import Builder
from .. import types
from ..freezedried import FreezeDried, ListFreezeDryer
from ..log import LogFile
from ..path import pushd
from ..shell import ShellArguments

_known_install_types = ('prefix', 'exec-prefix', 'bindir', 'libdir',
                        'includedir')

CommandsFD = ListFreezeDryer(ShellArguments)


@FreezeDried.fields(rehydrate={'build_commands': CommandsFD,
                               'deploy_commands': CommandsFD})
class CustomBuilder(Builder):
    type = 'custom'
    _version = 1

    @staticmethod
    def upgrade(config, version):
        return config

    def __init__(self, pkg, *, build_commands, deploy_commands=None,
                 **kwargs):
        super().__init__(pkg, **kwargs)

        path_bases = pkg.path_bases(builder=self)
        symbols = self._options.expr_symbols.augment(paths=path_bases)
        cmds_type = types.maybe(types.list_of(types.shell_args()), default=[])

        T = types.TypeCheck(locals(), symbols)
        T.build_commands(cmds_type)
        T.deploy_commands(cmds_type)

    def _execute(self, logfile, commands, **kwargs):
        for line in commands:
            line = line.fill(**kwargs)
            if line[0] == 'cd':
                with logfile.synthetic_command(line):
                    if len(line) != 2:
                        raise RuntimeError('invalid command format')
                    os.chdir(line[1])
            else:
                logfile.check_call(line)

    def build(self, pkgdir, srcdir):
        builddir = self._builddir(pkgdir)

        with LogFile.open(pkgdir, self.name) as logfile:
            with pushd(srcdir):
                self._execute(logfile, self.build_commands, srcdir=srcdir,
                              builddir=builddir)

    def deploy(self, pkgdir, srcdir):
        builddir = self._builddir(pkgdir)

        with LogFile.open(pkgdir, self.name, kind='deploy') as logfile:
            with pushd(builddir):
                self._execute(logfile, self.deploy_commands, srcdir=srcdir,
                              builddir=builddir)
