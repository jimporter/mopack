import os
import warnings

from . import BinaryPackage, PackageOptions
from .. import log
from ..iterutils import iterate, uniques
from ..shell import get_cmd


class ConanPackage(BinaryPackage):
    source = 'conan'

    class Options(PackageOptions):
        source = 'conan'

        def __init__(self):
            # XXX: Don't always emit pkg_config files once we support other
            # usage types.
            self.generator = ['pkg_config']
            self.build = []

        def __call__(self, *, build=None, generator=None, config_file=None,
                     child_config=False):
            if generator and generator not in self.generator:
                self.generator.append(generator)
            if build:
                self.build.extend(iterate(build))
                self.build = uniques(self.build)

    def __init__(self, name, remote, options=None, usage=None, **kwargs):
        usage = usage or usage or {'type': 'pkg-config', 'path': ''}
        super().__init__(name, usage=usage, _path_bases={'builddir'}, **kwargs)
        self.remote = remote
        self.options = options or {}

    @staticmethod
    def _installdir(pkgdir):
        return os.path.join(pkgdir, 'conan')

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

    def clean_post(self, pkgdir, new_package, quiet=False):
        if ( new_package and self.source == new_package.source and
             self._this_options.generator ==
             new_package._this_options.generator ):
            return False

        if not quiet:
            log.pkg_clean(self.name)
        if 'pkg_config' in self._this_options.generator:
            try:
                os.remove(os.path.join(pkgdir, 'conan', self.name + '.pc'))
            except FileNotFoundError:
                pass
        return True

    @classmethod
    def resolve_all(cls, pkgdir, packages):
        for i in packages:
            log.pkg_resolve(i.name, 'from {}'.format(cls.source))

        options = packages[0]._this_options
        os.makedirs(pkgdir, exist_ok=True)
        with open(os.path.join(pkgdir, 'conanfile.txt'), 'w') as conan:
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
            for i in options.generator:
                print(i, file=conan)

        conan = get_cmd(packages[0]._common_options.env, 'CONAN', 'conan')
        with log.LogFile.open(pkgdir, 'conan') as logfile:
            logfile.check_call(
                conan + ['install', '-if', cls._installdir(pkgdir)] +
                cls._build_opts(options.build) + ['--', pkgdir]
            )

        for i in packages:
            i.resolved = True

    def _get_usage(self, pkgdir, submodules):
        return self.usage.get_usage(submodules, None, self._installdir(pkgdir))

    @staticmethod
    def deploy_all(pkgdir, packages):
        if any(i.should_deploy for i in packages):
            warnings.warn('deploying not yet supported for conan packages')
