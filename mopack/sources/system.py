from . import BinaryPackage, Package, submodules_type
from .. import log, types
from ..package_defaults import package_default
from ..usage.path_system import SystemUsage


class SystemPackage(BinaryPackage):
    source = 'system'

    def __init__(self, name, include_path=types.Unset,
                 library_path=types.Unset, headers=types.Unset,
                 libraries=types.Unset, submodules=types.Unset, **kwargs):
        Package.__init__(self, name, **kwargs)
        self.submodules = package_default(submodules_type, name)(
            'submodules', submodules
        )
        self.usage = SystemUsage(
            name, include_path=include_path, library_path=library_path,
            headers=headers, libraries=libraries, submodules=self.submodules
        )

    def resolve(self, pkgdir, deploy_paths):
        log.info('resolving {!r} from {}'.format(self.name, self.source))

    def deploy(self, pkgdir):
        pass


def fallback_system_package(name, options):
    pkg = SystemPackage(name, config_file=None)
    pkg.set_options(options)
    return pkg
