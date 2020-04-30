from . import Package
from .. import log
from ..usage.system import SystemUsage


class SystemPackage(Package):
    source = 'system'

    @classmethod
    def resolve_all(cls, pkgdir, packages, deploy_paths):
        log.info('resolving {} from {}'.format(
            ', '.join(repr(i.name) for i in packages), cls.source
        ))

        usages = [SystemUsage().usage(None, None)] * len(packages)
        return cls._resolved_metadata_all(packages, usages)

    @staticmethod
    def deploy_all(pkgdir, packages):
        pass
