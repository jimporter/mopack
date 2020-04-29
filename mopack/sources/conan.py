import os
import warnings

from . import Package, PackageOptions
from .. import log
from ..usage import Usage, make_usage


class ConanPackage(Package):
    source = 'conan'
    _rehydrate_fields = {'usage': Usage}

    class Options(PackageOptions):
        source = 'conan'

        def __init__(self):
            # XXX: Don't always emit pkg_config files once we support other
            # usage types.
            self.generator = ['pkg_config']

        def __call__(self, *, generator=None, config_file=None,
                     child_config=False):
            if generator and generator not in self.generator:
                self.generator.append(generator)

    def __init__(self, name, remote, options=None, usage=None, **kwargs):
        super().__init__(name, **kwargs)
        self.remote = remote
        self.options = options or {}
        self.usage = make_usage(usage or {'type': 'pkg-config', 'path': ''})

    @property
    def remote_name(self):
        return self.remote.split('/')[0]

    def clean_post(self, pkgdir, new_package):
        if ( new_package and self.source == new_package.source and
             self.global_options.generator ==
             new_package.global_options.generator ):
            return False

        log.info('cleaning {!r}'.format(self.name))
        if 'pkg_config' in self.global_options.generator:
            try:
                os.remove(os.path.join(pkgdir, 'conan', self.name + '.pc'))
            except FileNotFoundError:
                pass
        return True

    @classmethod
    def resolve_all(cls, pkgdir, packages, deploy_paths):
        log.info('resolving {} from {}'.format(
            ', '.join(repr(i.name) for i in packages), cls.source
        ))

        global_options = packages[0].global_options
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
            for i in global_options.generator:
                print(i, file=conan)

        installdir = os.path.join(pkgdir, 'conan')
        with log.LogFile.open(pkgdir, 'conan') as logfile:
            logfile.check_call(['conan', 'install', '-if', installdir, pkgdir])

        usages = [i.usage.usage(os.path.abspath(installdir)) for i in packages]
        return cls._resolved_metadata_all(packages, usages)

    @staticmethod
    def deploy_all(pkgdir, packages):
        warnings.warn('deploying not supported for conan packages')
