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

        self.build_commands = types.maybe(types.list_of(
            types.shell_args(('srcdir', 'builddir'))
        ), [])('build_commands', build_commands)

        self.deploy_commands = types.maybe(types.list_of(
            types.shell_args(('builddir'))
        ), [])('deploy_commands', deploy_commands)

    def build(self, pkgdir, srcdir):
        builddir = self._builddir(pkgdir)

        with LogFile.open(pkgdir, self.name) as logfile:
            with pushd(srcdir):
                for line in self.build_commands:
                    logfile.check_call(line.fill(
                        srcdir=srcdir, builddir=builddir
                    ))

    def deploy(self, pkgdir):
        builddir = self._builddir(pkgdir)

        with LogFile.open(pkgdir, self.name, kind='deploy') as logfile:
            with pushd(builddir):
                for line in self.deploy_commands:
                    logfile.check_call(line.fill(builddir=builddir))
