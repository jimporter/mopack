from . import Package
from .. import log


class SystemPackage(Package):
    source = 'system'

    @classmethod
    def resolve_all(cls, pkgdir, packages, deploy_paths):
        log.info('resolving {} from {}'.format(
            ', '.join(repr(i.name) for i in packages), cls.source
        ))

        return cls._resolved_metadata_all(packages, {'type': 'system'})

    @staticmethod
    def deploy_all(pkgdir, packages):
        pass
