import os

from . import Package
from .. import log


class ConanPackage(Package):
    source = 'conan'

    def __init__(self, name, remote, options=None, **kwargs):
        super().__init__(name, **kwargs)
        self.remote = remote
        self.options = options or {}

    @property
    def remote_name(self):
        return self.remote.split('/')[0]

    def clean_needed(self, pkgdir, new_package):
        if new_package and new_package.source == self.source:
            return False

        log.info('cleaning {!r}'.format(self.name))
        try:
            os.remove(os.path.join(pkgdir, 'conan', self.name + '.pc'))
        except FileNotFoundError:
            pass
        return True

    @classmethod
    def resolve_all(cls, pkgdir, packages):
        log.info('resolving {} from {}'.format(
            ', '.join(repr(i.name) for i in packages), cls.source
        ))

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

        installdir = os.path.join(pkgdir, 'conan')
        with log.open_log(pkgdir, 'conan') as logfile:
            log.check_call_log(['conan', 'install', '-g', 'pkg_config',
                                '-if', installdir, pkgdir],
                               log=logfile)

        return cls._resolved_metadata_all(packages, {
            'type': 'pkgconfig', 'path': os.path.abspath(installdir)
        })
