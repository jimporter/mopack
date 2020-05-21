from . import BinaryPackage
from .. import log, types
from ..usage.system import SystemUsage


class SystemPackage(BinaryPackage):
    source = 'system'

    def __init__(self, name, headers=None, libraries=types.Unset, **kwargs):
        usage = SystemUsage(name, headers=headers, libraries=libraries)
        super().__init__(name, usage=usage, **kwargs)

    def resolve(self, pkgdir, deploy_paths):
        log.info('resolving {} from {}'.format(self.name, self.source))

    def deploy(self, pkgdir):
        pass


def fallback_system_package(name, options):
    pkg = SystemPackage(name, config_file=None)
    pkg.set_options(options)
    return pkg
