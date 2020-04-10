import json
import os
import shutil
import yaml

from .sources import make_package, Package

mopack_dirname = 'mopack'
metadata_filename = 'mopack.json'


class _PlaceholderPackage:
    def __repr__(self):
        return '<PlaceholderPackage>'


PlaceholderPackage = _PlaceholderPackage()


class Config:
    def __init__(self, filenames, parent=None):
        self.packages = {}
        self.parent = parent
        for f in reversed(filenames):
            self._accumulate_config(f)

    def _accumulate_config(self, filename):
        filename = os.path.abspath(filename)
        with open(filename) as f:
            next_config = yaml.safe_load(f)
            for k, v in next_config['packages'].items():
                if k in self.packages:
                    continue
                v['config_file'] = filename

                # If a parent package has already defined this package, just
                # store a placeholder to track it. Otherwise, make the real
                # package object.
                self.packages[k] = (PlaceholderPackage if self._in_parent(k)
                                    else make_package(k, v))

    def _in_parent(self, name):
        if not self.parent:
            return False
        return name in self.parent.packages or self.parent._in_parent(name)

    def _validate_children(self, children):
        # Ensure that there are no conflicting package definitions in any of
        # the children.
        by_name = {}
        for i in children:
            for k, v in i.packages.items():
                by_name.setdefault(k, []).append(v)
        for k, v in by_name.items():
            for i in range(1, len(v)):
                if v[0] != v[i]:
                    raise ValueError('conflicting definitions for package {!r}'
                                     .format(k))

    def add_children(self, children):
        self._validate_children(children)

        # XXX: It might be nicer to put a child's deps immediately before the
        # child, rather than at the beginning of the package list.
        new_packages = {}
        for i in children:
            for k, v in i.packages.items():
                # We have a package that's needed by another; put it in our
                # packages before the package that depends on it. If it's in
                # our list already, use that one; otherwise, use the child's
                # definition.
                new_packages[k] = self.packages.pop(k, v)
        new_packages.update(self.packages)
        self.packages = new_packages

    def __repr__(self):
        return '<Config({})>'.format(', '.join(
            repr(i) for i in self.packages.values()
        ))


def get_package_dir(builddir):
    return os.path.join(builddir, mopack_dirname)


def _metadata_path(pkgdir):
    return os.path.join(pkgdir, metadata_filename)


def get_metadata(pkgdir):
    with open(_metadata_path(pkgdir)) as f:
        return json.load(f)


def save_metadata(metadata, pkgdir):
    with open(_metadata_path(pkgdir), 'w') as f:
        json.dump(metadata, f)


def _get_old_packages(pkgdir):
    try:
        old_metadata = get_metadata(pkgdir)
        return {k: Package.rehydrate(v['config'])
                for k, v in old_metadata.items()}
    except FileNotFoundError:
        return {}


def clean(pkgdir):
    shutil.rmtree(pkgdir)


def fetch(config, pkgdir):
    os.makedirs(pkgdir, exist_ok=True)
    old_packages = _get_old_packages(pkgdir)
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

    metadata = {}
    for k, v in batch_packages.items():
        metadata.update(k.resolve_all(pkgdir, v))

    # Ensure metadata is up-to-date for each non-batch package so that they can
    # find any dependencies they need. XXX: Technically, we're looking to do
    # this for all *source* packages, but currently a package is non-batched
    # iff it's a source package. Revisit this when we have a better idea of
    # what the abstractions are.
    save_metadata(metadata, pkgdir)
    for i in packages:
        metadata[i.name] = i.resolve(pkgdir)
        save_metadata(metadata, pkgdir)
