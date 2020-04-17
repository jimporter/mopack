import json
import os
import shutil

from .config import Config, PlaceholderPackage
from .sources import Package

mopack_dirname = 'mopack'


def get_package_dir(builddir):
    return os.path.join(builddir, mopack_dirname)


class MetadataVersionError(RuntimeError):
    pass


class Metadata:
    metadata_filename = 'mopack.json'
    version = 1

    def __init__(self, deploy_paths=None):
        self.deploy_paths = deploy_paths or {}
        self.packages = {}

    def add_package(self, package):
        self.packages[package['config']['name']] = package

    def add_packages(self, packages):
        for i in packages:
            self.add_package(i)

    def rehydrate(self):
        return {k: Package.rehydrate(v['config'])
                for k, v in self.packages.items()}

    def save(self, pkgdir):
        with open(os.path.join(pkgdir, self.metadata_filename), 'w') as f:
            json.dump({
                'version': self.version,
                'metadata': {
                    'deploy_paths': self.deploy_paths,
                    'packages': self.packages,
                }
            }, f)

    @classmethod
    def load(cls, pkgdir):
        with open(os.path.join(pkgdir, cls.metadata_filename)) as f:
            state = json.load(f)
            version, data = state['version'], state['metadata']
        if version > cls.version:
            raise MetadataVersionError(
                'saved version exceeds expected version'
            )

        metadata = Metadata.__new__(Metadata)
        metadata.deploy_paths = data['deploy_paths']
        metadata.packages = data['packages']
        return metadata


def clean(pkgdir):
    shutil.rmtree(pkgdir)


def fetch(config, pkgdir):
    os.makedirs(pkgdir, exist_ok=True)
    try:
        old_packages = Metadata.load(pkgdir).rehydrate()
    except FileNotFoundError:
        old_packages = {}

    _do_fetch(config, pkgdir, old_packages)

    for i in old_packages.values():
        i.clean_needed(pkgdir, None)


def _do_fetch(config, pkgdir, old_packages):
    child_configs = []
    for i in config.packages.values():
        # If we have a placeholder package, a parent config has a definition
        # for it, so skip it.
        if i is PlaceholderPackage:
            continue

        # Clean out the old package if needed.
        old = old_packages.pop(i.name, None)
        if old:
            old.clean_needed(pkgdir, i)

        # Fetch the new package and check for child mopack configs.
        mopack = i.fetch(pkgdir)
        if mopack:
            child_configs.append(Config([mopack], parent=config))
            _do_fetch(child_configs[-1], pkgdir, old_packages)
    config.add_children(child_configs)


def resolve(config, pkgdir, deploy_paths=None):
    fetch(config, pkgdir)

    metadata = Metadata(deploy_paths)

    packages, batch_packages = [], {}
    for i in config.packages.values():
        if hasattr(i, 'resolve_all'):
            batch_packages.setdefault(type(i), []).append(i)
        else:
            packages.append(i)

    for k, v in batch_packages.items():
        metadata.add_packages(k.resolve_all(pkgdir, v, metadata.deploy_paths))

    # Ensure metadata is up-to-date for each non-batch package so that they can
    # find any dependencies they need. XXX: Technically, we're looking to do
    # this for all *source* packages, but currently a package is non-batched
    # iff it's a source package. Revisit this when we have a better idea of
    # what the abstractions are.
    metadata.save(pkgdir)
    for i in packages:
        metadata.add_package(i.resolve(pkgdir,  metadata.deploy_paths))
        metadata.save(pkgdir)


def deploy(pkgdir):
    metadata = Metadata.load(pkgdir)

    packages, batch_packages = [], {}
    for i in metadata.rehydrate().values():
        if hasattr(i, 'deploy_all'):
            batch_packages.setdefault(type(i), []).append(i)
        else:
            packages.append(i)

    for k, v in batch_packages.items():
        k.deploy_all(pkgdir, v)
    for i in packages:
        i.deploy(pkgdir)


def usage(pkgdir, name, strict=False):
    metadata = Metadata.load(pkgdir)
    return dict(name=name, **metadata.packages[name]['usage'])
