import os
import shutil

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
class B2Builder(DirectoryBuilder):
    type = 'b2'
    _version = 1

    @staticmethod
    def upgrade(config, version):
        return config

    def __init__(self, pkg, *, directory=None, extra_args=None, _symbols,
                 **kwargs):
        _symbols = _symbols.augment_path_bases(*self.path_bases())
        if directory is None and _symbols.path_bases:
            # Default to the last directory before the builddir.
            directory = '$' + _symbols.path_bases[-2]

        super().__init__(pkg, _symbols=_symbols, directory=directory, **kwargs)

        T = types.TypeCheck(locals(), _symbols)
        T.extra_args(types.shell_args(none_ok=True))

    def path_bases(self):
        return ('builddir',)

    def path_values(self, metadata, parent_values):
        builddir = os.path.join(self.directory.string(**parent_values),
                                'stage')
        return {'builddir': builddir}

    def clean(self, metadata, pkg):
        path_values = pkg.path_values(metadata)
        shutil.rmtree(path_values['builddir'], ignore_errors=True)

    def build(self, metadata, pkg):
        path_values = pkg.path_values(metadata)

        env = self._common_options.env
        b2 = get_cmd(env, 'B2', './b2')
        with LogFile.open(metadata.pkgdir, self.name) as logfile:
            with pushd(self.directory.string(**path_values)):
                logfile.check_call(b2 + self.extra_args.fill(**path_values),
                                   env=env)

    def deploy(self, metadata, pkg):
        path_values = pkg.path_values(metadata)

        env = self._common_options.env
        b2 = get_cmd(env, 'B2', './b2')
        with LogFile.open(metadata.pkgdir, self.name,
                          kind='deploy') as logfile:
            with pushd(self.directory.string(**path_values)):
                logfile.check_call(b2 + ['install'], env=env)
