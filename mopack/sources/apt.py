from . import Package
from .. import log


class AptPackage(Package):
    source = 'apt'

    def __init__(self, name, remote=None, **kwargs):
        super().__init__(name, **kwargs)
        # XXX: Add support for repositories.
        self.remote = remote or 'lib{}-dev'.format(name)

    @classmethod
    def resolve_all(cls, pkgdir, packages):
        log.info('resolving {} from {}'.format(
            ', '.join(repr(i.name) for i in packages), cls.source
        ))

        remotes = [i.remote for i in packages]
        with log.open_log(pkgdir, 'apt') as logfile:
            log.check_call_log(['sudo', 'apt-get', 'install', '-y'] + remotes,
                               log=logfile)

        return cls._resolved_metadata_all(packages, {'type': 'system'})
