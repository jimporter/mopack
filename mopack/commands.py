import os
import shutil

from . import log
from .config import PlaceholderPackage
from .exceptions import ConfigurationError
from .metadata import Metadata

mopack_dirname = 'mopack'


def get_package_dir(builddir):
    return os.path.abspath(os.path.join(builddir, mopack_dirname))


class PackageTreeItem:
    def __init__(self, package, version, children=None):
        self.package = package
        self.version = version
        self.children = children or []


def clean(pkgdir):
    shutil.rmtree(pkgdir)


def _do_fetch(config, old_metadata, pkgdir):
    child_configs = []
    for pkg in config.packages.values():
        # If we have a placeholder package, a parent config has a definition
        # for it, so skip it.
        if pkg is PlaceholderPackage:
            continue

        # Clean out the old package sources if needed.
        if pkg.name in old_metadata.packages:
            old_metadata.packages[pkg.name].clean_pre(pkg, pkgdir)

        # Fetch the new package and check for child mopack configs.
        try:
            child_config = pkg.fetch(config, pkgdir)
        except Exception:
            pkg.clean_pre(None, pkgdir, quiet=True)
            raise

        if child_config:
            child_configs.append(child_config)
            _do_fetch(child_config, old_metadata, pkgdir)
    config.add_children(child_configs)


def _fill_metadata(config):
    config.finalize()
    metadata = Metadata(config.options, config.files, config.implicit_files)
    for pkg in config.packages.values():
        metadata.add_package(pkg)
    return metadata


def fetch(config, pkgdir):
    log.LogFile.clean_logs(pkgdir)

    old_metadata = Metadata.try_load(pkgdir)
    try:
        _do_fetch(config, old_metadata, pkgdir)
    except ConfigurationError:
        raise
    except Exception:
        _fill_metadata(config).save(pkgdir)
        raise

    metadata = _fill_metadata(config)

    # Clean out old package data if needed.
    for pkg in config.packages.values():
        old = old_metadata.packages.pop(pkg.name, None)
        if old:
            old.clean_post(pkg, pkgdir)

    # Clean removed packages.
    for pkg in old_metadata.packages.values():
        pkg.clean_all(None, pkgdir)

    return metadata


def resolve(config, pkgdir):
    if not config:
        log.info('no inputs')
        return

    metadata = fetch(config, pkgdir)

    packages, batch_packages = [], {}
    for pkg in metadata.packages.values():
        if hasattr(pkg, 'resolve_all'):
            batch_packages.setdefault(type(pkg), []).append(pkg)
        else:
            packages.append(pkg)

    for t, pkgs in batch_packages.items():
        try:
            t.resolve_all(pkgs, pkgdir)
        except Exception:
            for i in pkgs:
                i.clean_post(None, pkgdir, quiet=True)
            metadata.save(pkgdir)
            raise

    for pkg in packages:
        try:
            # Ensure metadata is up-to-date for packages that need it.
            if pkg.needs_dependencies:
                metadata.save(pkgdir)
            pkg.resolve(pkgdir)
        except Exception:
            pkg.clean_post(None, pkgdir, quiet=True)
            metadata.save(pkgdir)
            raise

    metadata.save(pkgdir)


def deploy(pkgdir):
    log.LogFile.clean_logs(pkgdir, kind='deploy')
    metadata = Metadata.load(pkgdir)

    packages, batch_packages = [], {}
    for pkg in metadata.packages.values():
        if not pkg.resolved:
            raise ValueError('package {!r} has not been resolved successfully'
                             .format(pkg.name))
        if hasattr(pkg, 'deploy_all'):
            batch_packages.setdefault(type(pkg), []).append(pkg)
        else:
            packages.append(pkg)

    for t, pkgs in batch_packages.items():
        t.deploy_all(pkgs, pkgdir)
    for pkg in packages:
        pkg.deploy(pkgdir)


def usage(pkgdir, name, submodules=None, strict=False):
    try:
        metadata = Metadata.load(pkgdir)
    except FileNotFoundError:
        if strict:
            raise
        metadata = Metadata()

    package = metadata.get_package(name, strict)
    return package.get_usage(submodules, pkgdir)


def list_files(pkgdir, implicit=False, strict=False):
    try:
        metadata = Metadata.load(pkgdir)
        if implicit:
            return metadata.files + metadata.implicit_files
        return metadata.files
    except FileNotFoundError:
        if strict:
            raise
        return []


def list_packages(pkgdir, flat=False):
    metadata = Metadata.load(pkgdir)

    if flat:
        return [PackageTreeItem(pkg, pkg.version(pkgdir)) for pkg in
                metadata.packages.values()]

    packages = []
    pending = {}
    for pkg in metadata.packages.values():
        item = PackageTreeItem(pkg, pkg.version(pkgdir),
                               pending.pop(pkg.name, None))
        if pkg.parent:
            pending.setdefault(pkg.parent, []).append(item)
        else:
            packages.append(item)
    return packages
