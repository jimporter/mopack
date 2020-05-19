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
        log.info('resolving {} from {}'.format(
            ', '.join(repr(i.name) for i in packages), cls.source
        ))

        remotes = [i.remote for i in packages]
        with log.LogFile.open(pkgdir, 'apt') as logfile:
            logfile.check_call(['sudo', 'apt-get', 'install', '-y'] + remotes)

        usages = [i.usage.usage(None, None) for i in packages]
        return cls._resolved_metadata_all(packages, usages)

    @staticmethod
    def deploy_all(pkgdir, packages):
        pass
