from . import BinaryPackage, Package, submodules_type
from .. import log
from ..types import Unset
from ..usage.path_system import SystemUsage


class SystemPackage(BinaryPackage):
    source = 'system'

    def __init__(self, name, auto_link=Unset, include_path=Unset,
                 library_path=Unset, headers=Unset, libraries=Unset,
                 compile_flags=Unset, link_flags=Unset, submodules=Unset,
                 **kwargs):
        Package.__init__(self, name, **kwargs)
        self.submodules = self._package_default(submodules_type, name)(
            'submodules', submodules
        )
        self.usage = SystemUsage(
            name, auto_link=auto_link, include_path=include_path,
            library_path=library_path, headers=headers, libraries=libraries,
            compile_flags=compile_flags, link_flags=link_flags,
            submodules=self.submodules
        )

    def resolve(self, pkgdir, deploy_paths):
        log.pkg_resolve(self.name, 'from {}'.format(self.source))

    def deploy(self, pkgdir):
        pass


def fallback_system_package(name, options):
    pkg = SystemPackage(name, config_file=None)
    pkg.set_options(options)
    return pkg
