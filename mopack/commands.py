import json
import os
import shutil

from . import log
from .builders import BuilderOptions
from .config import CommonOptions, Config, PlaceholderPackage
from .exceptions import ConfigurationError
from .freezedried import DictKeysFreezeDryer, DictToListFreezeDryer
from .sources import Package, PackageOptions
from .sources.system import fallback_system_package

mopack_dirname = 'mopack'


def get_package_dir(builddir):
    return os.path.abspath(os.path.join(builddir, mopack_dirname))


BuilderOptsFD = DictToListFreezeDryer(BuilderOptions, lambda x: x.type)
PackageOptsFD = DictToListFreezeDryer(PackageOptions, lambda x: x.source)
OptionsFD = DictKeysFreezeDryer(common=CommonOptions, builders=BuilderOptsFD,
                                sources=PackageOptsFD)

PackagesFD = DictToListFreezeDryer(Package, lambda x: x.name)


class MetadataVersionError(RuntimeError):
    pass


class Metadata:
    metadata_filename = 'mopack.json'
    version = 1

    def __init__(self, deploy_paths=None, options=None, files=None,
                 implicit_files=None):
        self.deploy_paths = deploy_paths or {}
        self.options = options or Config.default_options()
        self.files = files or []
        self.implicit_files = implicit_files or []
        self.packages = {}

    def add_package(self, package):
        self.packages[package.name] = package

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
                    'deploy_paths': self.deploy_paths,
                    'options': OptionsFD.dehydrate(self.options),
                    'packages': PackagesFD.dehydrate(self.packages),
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

        metadata.files = state['config_files']['explicit']
        metadata.implicit_files = state['config_files']['implicit']

        metadata.options = OptionsFD.rehydrate(data['options'])
        metadata.packages = PackagesFD.rehydrate(data['packages'])
        for pkg in metadata.packages.values():
            pkg.set_options(metadata.options)

        return metadata

    @classmethod
    def try_load(cls, pkgdir):
        try:
            return Metadata.load(pkgdir)
        except FileNotFoundError:
            return Metadata()


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
            old_metadata.packages[pkg.name].clean_pre(pkgdir, pkg)

        # Fetch the new package and check for child mopack configs.
        try:
            child_config = pkg.fetch(pkgdir, parent_config=config)
        except Exception:
            pkg.clean_pre(pkgdir, None, quiet=True)
            raise

        if child_config:
            child_configs.append(child_config)
            _do_fetch(child_config, old_metadata, pkgdir)
    config.add_children(child_configs)


def _fill_metadata(config, deploy_paths):
    config.finalize()
    metadata = Metadata(deploy_paths, config.options, config.files,
                        config.implicit_files)
    for pkg in config.packages.values():
        metadata.add_package(pkg)
    return metadata


def fetch(config, pkgdir, deploy_paths=None):
    log.LogFile.clean_logs(pkgdir)

    old_metadata = Metadata.try_load(pkgdir)
    try:
        _do_fetch(config, old_metadata, pkgdir)
    except ConfigurationError:
        raise
    except Exception:
        _fill_metadata(config, deploy_paths).save(pkgdir)
        raise

    metadata = _fill_metadata(config, deploy_paths)

    # Clean out old package data if needed.
    for pkg in config.packages.values():
        old = old_metadata.packages.pop(pkg.name, None)
        if old:
            old.clean_post(pkgdir, pkg)

    # Clean removed packages.
    for pkg in old_metadata.packages.values():
        pkg.clean_all(pkgdir, None)

    return metadata


def resolve(config, pkgdir, deploy_paths=None):
    if not config:
        log.info('no inputs')
        return

    metadata = fetch(config, pkgdir, deploy_paths)

    packages, batch_packages = [], {}
    for pkg in config.packages.values():
        if hasattr(pkg, 'resolve_all'):
            batch_packages.setdefault(type(pkg), []).append(pkg)
        else:
            packages.append(pkg)

    for t, pkgs in batch_packages.items():
        try:
            t.resolve_all(pkgdir, pkgs, metadata.deploy_paths)
        except Exception:
            for i in pkgs:
                i.clean_post(pkgdir, None, quiet=True)
            metadata.save(pkgdir)
            raise

    # Ensure metadata is up-to-date for each non-batch package so that they can
    # find any dependencies they need. XXX: Technically, we're looking to do
    # this for all *source* packages, but currently a package is non-batched
    # iff it's a source package. Revisit this when we have a better idea of
    # what the abstractions are.
    metadata.save(pkgdir)
    for pkg in packages:
        try:
            pkg.resolve(pkgdir, metadata.deploy_paths)
            metadata.save(pkgdir)
        except Exception:
            pkg.clean_post(pkgdir, None, quiet=True)
            raise


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
        t.deploy_all(pkgdir, pkgs)
    for pkg in packages:
        pkg.deploy(pkgdir)


def usage(pkgdir, name, submodules=None, strict=False):
    package = None
    try:
        metadata = Metadata.load(pkgdir)
        if name in metadata.packages:
            package = metadata.packages[name]
        elif strict:
            raise ValueError('no definition for package {!r}'.format(name))
    except FileNotFoundError:
        if strict:
            raise
        metadata = Metadata()

    if package is None:
        package = fallback_system_package(name, metadata.options)

    if not package.resolved:
        raise ValueError('package {!r} has not been resolved successfully'
                         .format(name))
    return dict(name=name, **package.get_usage(pkgdir, submodules))


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
