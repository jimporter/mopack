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
    _path_bases = ('srcdir', 'builddir')

    def __init__(self, name, *, build_commands, deploy_commands=None,
                 submodules, **kwargs):
        super().__init__(name, **kwargs)

        cmds_type = types.maybe(types.list_of(
            types.shell_args(self._path_bases)
        ), [])
        self.build_commands = cmds_type('build_commands', build_commands)
        self.deploy_commands = cmds_type('deploy_commands', deploy_commands)

    def _execute(self, logfile, commands, **kwargs):
        for line in commands:
            logfile.check_call(line.fill(**kwargs))

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
