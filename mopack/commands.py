import json
import os
import shutil

from .config import Config, PlaceholderPackage
from .sources import Package

mopack_dirname = 'mopack'


def get_package_dir(builddir):
    return os.path.join(builddir, mopack_dirname)


class Metadata:
    metadata_filename = 'mopack.json'

    def __init__(self):
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
            json.dump(self.packages, f)

    @classmethod
    def load(cls, pkgdir):
        metadata = Metadata.__new__(Metadata)
        with open(os.path.join(pkgdir, cls.metadata_filename)) as f:
            metadata.packages = json.load(f)
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


def resolve(config, pkgdir):
    fetch(config, pkgdir)

    packages, batch_packages = [], {}
    for i in config.packages.values():
        if hasattr(i, 'resolve_all'):
            batch_packages.setdefault(type(i), []).append(i)
        else:
            packages.append(i)

    metadata = Metadata()
    for k, v in batch_packages.items():
        metadata.add_packages(k.resolve_all(pkgdir, v))

    # Ensure metadata is up-to-date for each non-batch package so that they can
    # find any dependencies they need. XXX: Technically, we're looking to do
    # this for all *source* packages, but currently a package is non-batched
    # iff it's a source package. Revisit this when we have a better idea of
    # what the abstractions are.
    metadata.save(pkgdir)
    for i in packages:
        metadata.add_package(i.resolve(pkgdir))
        metadata.save(pkgdir)
