import os
import subprocess
import warnings
from itertools import chain

from . import BatchPackage, BinaryPackage, PackageOptions
from .. import log, types
from ..environment import get_cmd
from ..freezedried import GenericFreezeDried
from ..iterutils import uniques
from ..objutils import Unset
from ..path import pushd
from ..shell import ShellArguments


class ConanPackage(BinaryPackage, BatchPackage):
    origin = 'conan'
    _version = 2

    @GenericFreezeDried.fields(rehydrate={'extra_args': ShellArguments})
    class Options(PackageOptions):
        origin = 'conan'
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
                T.build(types.list_of(types.string, listify=True),
                        reducer=lambda a, b: uniques(chain(a, b)))
            if extra_args:
                T.extra_args(types.shell_args(), reducer=lambda a, b: a + b)

    @staticmethod
    def upgrade(config, version):
        # v2 moves `submodules.required` to `submodule_required` and stores
        # `submodules` as a dict of submodule names.
        if version < 2:
            if config['submodules']:
                config['submodule_required'] = config['submodules']['required']
                config['submodules'] = {
                    i: {} for i in config['submodules']['names']
                }

        return config

    # TODO: Remove `usage` after v0.2 is released.
    def __init__(self, name, remote, build=False, options=None,
                 linkage=Unset, usage=Unset, **kwargs):
        if linkage is Unset and usage is Unset:
            linkage = {'type': 'pkg_config', 'pkg_config_path': ''}
        super().__init__(name, linkage=linkage, usage=usage, **kwargs)

        T = types.TypeCheck(locals(), self._expr_symbols)
        T.remote(types.string)
        T.build(types.boolean)

        value_type = types.one_of(types.string, types.boolean, desc='a value')
        T.options(types.maybe(types.dict_of(types.string, value_type), {}))

    @property
    def _linkage_expr_symbols(self):
        return self._options.expr_symbols.augment(path_bases=['builddir'])

    def path_bases(self, *, builder=None):
        return ('builddir',) if builder else ()

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

    def path_values(self, metadata):
        result = super().path_values(metadata)
        result['builddir'] = self._installdir(metadata)
        return result

    def version(self, metadata):
        # Inspect the local conan cache to get the package's version.
        # XXX: There might be a better way to do this...
        conan = get_cmd(self._common_options.env, 'CONAN', 'conan')
        return subprocess.run(
            conan + ['inspect', '--raw=version', self.remote],
            check=True, stdout=subprocess.PIPE, universal_newlines=True
        ).stdout

    def clean_post(self, metadata, new_package, quiet=False):
        if new_package and self.origin == new_package.origin:
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
            log.pkg_resolve(i.name, 'from {}'.format(cls.origin))

        options = packages[0]._this_options
        conandir = cls._installdir(metadata)
        os.makedirs(conandir, exist_ok=True)

        # XXX: Rather than putting the conanfile in the `mopack/conan`
        # directory, we could look into using Conan 2.0's "layouts" feature.
        with open(os.path.join(conandir, 'conanfile.txt'),
                  'w') as conan:
            print('[requires]', file=conan)
            for i in packages:
                print(i.remote, file=conan)
            print('', file=conan)

            print('[options]', file=conan)
            for i in packages:
                for k, v in i.options.items():
                    print('{}*:{}={}'.format(i.remote_name, k, v), file=conan)
            print('', file=conan)

            print('[generators]', file=conan)
            print('PkgConfigDeps', file=conan)

        build = [i.remote_name for i in packages if i.build]

        env = packages[0]._common_options.env
        conan = get_cmd(env, 'CONAN', 'conan')
        # XXX: We run this from the `mopack/conan` directory so that we can use
        # the same command in Conan 1.x and 2.x and still get the generated
        # files in the right place. Maybe it would be better to use different
        # command arguments depending on Conan's version.
        with log.LogFile.open(metadata.pkgdir, 'conan') as logfile, \
             pushd(conandir):
            logfile.check_call(
                conan + ['install'] +
                cls._build_opts(uniques(options.build + build)) +
                options.extra_args.args() + ['--', conandir],
                env=env
            )

        super(ConanPackage, cls).resolve_all(metadata, packages)

    @classmethod
    def deploy_all(cls, metadata, packages):
        if any(i.should_deploy for i in packages):
            warnings.warn('deploying not yet supported for conan packages')
