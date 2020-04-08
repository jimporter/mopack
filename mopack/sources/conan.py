import os

from . import Package
from ..log import check_call_log, open_log


class ConanPackage(Package):
    def __init__(self, name, remote, options=None, **kwargs):
        super().__init__(name, **kwargs)
        self.remote = remote
        self.options = options or {}

    @property
    def remote_name(self):
        return self.remote.split('/')[0]

    @staticmethod
    def resolve_all(pkgdir, packages):
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
        with open_log(pkgdir, 'conan') as log:
            check_call_log(['conan', 'install', '-g', 'pkg_config',
                            '-if', installdir, pkgdir],
                           log=log)

        return {i.name: {
            'source': 'conan',
            'remote': i.remote,
            'usage': {'type': 'pkgconfig', 'path': os.path.abspath(installdir)}
        } for i in packages}
