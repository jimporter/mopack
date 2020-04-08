from . import Package
from ..log import check_call_log, open_log


class AptPackage(Package):
    def __init__(self, name, remote=None, **kwargs):
        super().__init__(name, **kwargs)
        # XXX: Add support for repositories.
        self.remote = remote or 'lib{}-dev'.format(name)

    @staticmethod
    def resolve_all(pkgdir, packages):
        remotes = [i.remote for i in packages]
        with open_log(pkgdir, 'apt') as log:
            check_call_log(['sudo', 'apt-get', 'install', '-y'] + remotes,
                           log=log)

        return {i.name: {
            'source': 'apt',
            'remote': i.remote,
            'usage': {'type': 'system'}
        } for i in packages}
