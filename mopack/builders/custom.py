import warnings

from . import Builder
from .. import types
from ..freezedried import FreezeDried, ListFreezeDryer
from ..log import LogFile
from ..path import auto_path_string, PathOrStrFreezeDryer, pushd

_known_install_types = ('prefix', 'exec-prefix', 'bindir', 'libdir',
                        'includedir')

CommandsFD = ListFreezeDryer(ListFreezeDryer(PathOrStrFreezeDryer))


@FreezeDried.fields(rehydrate={'build_commands': CommandsFD})
class CustomBuilder(Builder):
    type = 'custom'
    _path_bases = ('srcdir', 'builddir')

    def __init__(self, name, *, build_commands, submodules, **kwargs):
        super().__init__(name, **kwargs)

        cmds_type = types.maybe(types.list_of(
            types.shell_args(self._path_bases)
        ), [])
        self.build_commands = cmds_type('build_commands', build_commands)

    def build(self, pkgdir, srcdir):
        builddir = self._builddir(pkgdir)

        with LogFile.open(pkgdir, self.name) as logfile:
            with pushd(srcdir):
                for line in self.build_commands:
                    logfile.check_call([auto_path_string(
                        i, srcdir=srcdir, builddir=builddir
                    ) for i in line])

    def deploy(self, pkgdir):
        warnings.warn('deploying not yet supported for custom builders')
