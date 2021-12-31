import os
import subprocess
import warnings

from . import BinaryPackage, PackageOptions
from .. import log, types
from ..environment import get_cmd
from ..freezedried import FreezeDried
from ..iterutils import uniques
from ..shell import ShellArguments


class ConanPackage(BinaryPackage):
    source = 'conan'
    _version = 1

    @FreezeDried.fields(rehydrate={'extra_args': ShellArguments})
    class Options(PackageOptions):
        source = 'conan'
        _version = 1

        @staticmethod
        def upgrade(config, version):
            return config

        def __init__(self):
            self.build = []
            self.extra_args = ShellArguments()

        def __call__(self, *, build=None, extra_args=None, config_file,
                     _symbols, _child_config=False):
            T = types.TypeCheck(locals(), _symbols)
            if build:
                T.build(types.list_of(types.string, listify=True), extend=True)
                self.build = uniques(self.build)
            if extra_args:
                T.extra_args(types.shell_args(), extend=True)

    @staticmethod
    def upgrade(config, version):
        return config

    def __init__(self, name, remote, build=False, options=None, usage=None,
                 **kwargs):
        usage = usage or {'type': 'pkg_config', 'pkg_config_path': ''}
        super().__init__(name, usage=usage, **kwargs)

        T = types.TypeCheck(locals(), self._expr_symbols)
        T.remote(types.string)
        T.build(types.boolean)

        value_type = types.one_of(types.string, types.boolean, desc='a value')
        T.options(types.maybe(types.dict_of(types.string, value_type), {}))

    @staticmethod
    def _installdir(metadata):
        return os.path.join(metadata.pkgdir, 'conan')

    @staticmethod
    def _build_opts(value):
        if not value:
            return []
        elif 'all' in value:
            return ['--build']
        else:
            return ['--build=' + i for i in value]

    @property
    def remote_name(self):
        return self.remote.split('/')[0]

    def path_bases(self, *, builder=None):
        return ('builddir',) if builder else ()

    def path_values(self, metadata, *, builder=None):
        return {'builddir': self._installdir(metadata)} if builder else {}

    def version(self, metadata):
        # Inspect the local conan cache to get the package's version.
        # XXX: There might be a better way to do this...
        conan = get_cmd(self._common_options.env, 'CONAN', 'conan')
        return subprocess.run(
            conan + ['inspect', '--raw=version', self.remote],
            check=True, stdout=subprocess.PIPE, universal_newlines=True
        ).stdout

    def clean_post(self, metadata, new_package, quiet=False):
        if new_package and self.source == new_package.source:
            return False

        if not quiet:
            log.pkg_clean(self.name)

        try:
            # Remove generated pkg-config file.
            os.remove(os.path.join(self._installdir(metadata),
                                   self.name + '.pc'))
        except FileNotFoundError:
            pass
        return True

    @classmethod
    def resolve_all(cls, metadata, packages):
        for i in packages:
            log.pkg_resolve(i.name, 'from {}'.format(cls.source))

        options = packages[0]._this_options
        os.makedirs(metadata.pkgdir, exist_ok=True)
        with open(os.path.join(metadata.pkgdir, 'conanfile.txt'),
                  'w') as conan:
            print('[requires]', file=conan)
            for i in packages:
                print(i.remote, file=conan)
            print('', file=conan)

            print('[options]', file=conan)
            for i in packages:
                for k, v in i.options.items():
                    print('{}:{}={}'.format(i.remote_name, k, v), file=conan)
            print('', file=conan)

            print('[generators]', file=conan)
            print('pkg_config', file=conan)

        build = [i.remote_name for i in packages if i.build]

        conan = get_cmd(packages[0]._common_options.env, 'CONAN', 'conan')
        with log.LogFile.open(metadata.pkgdir, 'conan') as logfile:
            logfile.check_call(
                conan + ['install', '-if', cls._installdir(metadata)] +
                cls._build_opts(uniques(options.build + build)) +
                options.extra_args.fill() + ['--', metadata.pkgdir]
            )

        for i in packages:
            i.resolved = True

    @staticmethod
    def deploy_all(metadata, packages):
        if any(i.should_deploy for i in packages):
            warnings.warn('deploying not yet supported for conan packages')
