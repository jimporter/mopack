from . import Package
from ..log import check_call_log, open_log


class AptPackage(Package):
    def __init__(self, name, depends=None, **kwargs):
        super().__init__(name, **kwargs)
        # XXX: Add support for repositories.
        self.depends = depends or [name]

    @staticmethod
    def fetch_all(pkgdir, packages):
        depends = sum((i.depends for i in packages), [])
        with open_log(pkgdir, 'apt') as log:
            check_call_log(['sudo', 'apt-get', 'install', '-y'] + depends,
                           log=log)
        return {i.name: {'usage': 'apt'} for i in packages}
