import os
import shutil

from . import DirectoryBuilder
from .. import types
from ..environment import get_cmd
from ..freezedried import GenericFreezeDried
from ..log import LogFile
from ..path import pushd
from ..shell import ShellArguments

_known_install_types = ('prefix', 'exec-prefix', 'libdir', 'includedir')


@GenericFreezeDried.fields(rehydrate={'extra_args': ShellArguments})
class B2Builder(DirectoryBuilder):
    type = 'b2'
    _version = 1

    @staticmethod
    def upgrade(config, version):
        return config

    def __init__(self, pkg, *, extra_args=None, _symbols, **kwargs):
        super().__init__(pkg, _symbols=_symbols, **kwargs)

        T = types.TypeCheck(locals(), _symbols)
        T.extra_args(types.shell_args(none_ok=True))

    def path_bases(self):
        return ('builddir', 'stagedir')

    def path_values(self, metadata, parent_values):
        builddir = os.path.abspath(os.path.join(metadata.pkgdir, 'build',
                                                self.name))
        return {'builddir': builddir,
                'stagedir': os.path.join(builddir, 'stage')}

    def _builddir_args(self, builddir):
        return ['--build-dir=' + builddir,
                '--stagedir=' + os.path.join(builddir, 'stage')]

    def _install_args(self, deploy_dirs):
        args = []
        for k, v in deploy_dirs.items():
            if k in _known_install_types:
                args.extend(['--{}={}'.format(k, v)])
        return args

    def clean(self, metadata, pkg):
        path_values = pkg.path_values(metadata)
        shutil.rmtree(path_values['builddir'], ignore_errors=True)

    def build(self, metadata, pkg):
        path_values = pkg.path_values(metadata)

        env = self._full_env.value(path_values)
        b2 = get_cmd(env, 'B2', 'b2')
        with LogFile.open(metadata.pkgdir, self.name) as logfile:
            with pushd(self.directory.string(path_values)):
                logfile.check_call(
                    b2 + self._builddir_args(path_values['builddir']) +
                    self.extra_args.args(path_values),
                    env=env
                )

    def deploy(self, metadata, pkg):
        path_values = pkg.path_values(metadata)

        env = self._full_env.value(path_values)
        b2 = get_cmd(env, 'B2', 'b2')
        with LogFile.open(metadata.pkgdir, self.name,
                          kind='deploy') as logfile:
            with pushd(self.directory.string(path_values)):
                logfile.check_call(
                    b2 + ['install'] +
                    self._builddir_args(path_values['builddir']) +
                    self._install_args(self._common_options.deploy_dirs) +
                    self.extra_args.args(path_values),
                    env=env
                )
