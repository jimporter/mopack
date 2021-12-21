import json
import os

from .config import Options
from .freezedried import DictToListFreezeDryer
from .sources import Package
from .sources.system import fallback_system_package


class MetadataVersionError(RuntimeError):
    pass


class Metadata:
    _PackagesFD = DictToListFreezeDryer(Package, lambda x: x.name)
    metadata_filename = 'mopack.json'
    version = 1

    def __init__(self, options=None, files=None, implicit_files=None):
        self.options = options or Options.default()
        self.files = files or []
        self.implicit_files = implicit_files or []
        self.packages = {}

    def add_package(self, package):
        self.packages[package.name] = package

    def get_package(self, name, strict=False):
        if name in self.packages:
            package = self.packages[name]
        elif strict:
            raise ValueError('no definition for package {!r}'.format(name))
        else:
            package = fallback_system_package(name, self.options)

        if not package.resolved:
            raise ValueError('package {!r} has not been resolved successfully'
                             .format(name))
        return package

    def save(self, pkgdir):
        os.makedirs(pkgdir, exist_ok=True)
        with open(os.path.join(pkgdir, self.metadata_filename), 'w') as f:
            json.dump({
                'version': self.version,
                'config_files': {
                    'explicit': self.files,
                    'implicit': self.implicit_files,
                },
                'metadata': {
                    'options': self.options.dehydrate(),
                    'packages': self._PackagesFD.dehydrate(self.packages),
                }
            }, f)

    @classmethod
    def load(cls, pkgdir):
        with open(os.path.join(pkgdir, cls.metadata_filename)) as f:
            state = json.load(f)
            version, data = state['version'], state['metadata']
        if version > cls.version:
            raise MetadataVersionError(
                'saved version {} exceeds expected version {}'
                .format(version, cls.version)
            )

        metadata = Metadata.__new__(Metadata)
        metadata.files = state['config_files']['explicit']
        metadata.implicit_files = state['config_files']['implicit']

        metadata.options = Options.rehydrate(data['options'])
        metadata.packages = cls._PackagesFD.rehydrate(
            data['packages'], _options=metadata.options
        )

        return metadata

    @classmethod
    def try_load(cls, pkgdir, strict=False):
        try:
            return Metadata.load(pkgdir)
        except FileNotFoundError:
            if strict:
                raise
            return Metadata()
