from . import BinaryPackage
from .. import log


class AptPackage(BinaryPackage):
    source = 'apt'

    def __init__(self, name, remote=None, usage='system', **kwargs):
        super().__init__(name, usage=usage, **kwargs)
        # XXX: Add support for repositories.
        self.remote = remote or 'lib{}-dev'.format(name)

    @classmethod
    def resolve_all(cls, pkgdir, packages, deploy_paths):
        for i in packages:
            log.pkg_resolve(i.name, 'from {}'.format(cls.source))

        remotes = [i.remote for i in packages]
        with log.LogFile.open(pkgdir, 'apt') as logfile:
            logfile.check_call(['sudo', 'apt-get', 'install', '-y'] + remotes)

    @staticmethod
    def deploy_all(pkgdir, packages):
        pass
