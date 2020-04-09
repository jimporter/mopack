import json
import os
import yaml

from .sources import make_package

mopack_dirname = 'mopack'
metadata_filename = 'mopack.json'


def get_package_dir(builddir):
    return os.path.join(builddir, mopack_dirname)


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
                if k in self.packages or (self.parent and
                                          k in self.parent.packages):
                    continue
                v['_config_file'] = filename
                self.packages[k] = make_package(k, v)

    def add_children(self, children):
        # FIXME: Check if there are any conflicting deps in any of the
        # children. XXX: Also, it might be nicer to put a child's deps
        # immediately before the child, rather than at the beginning of the
        # package list.
        new_packages = {}
        for i in children:
            for k, v in i.packages.items():
                if k not in self.packages:
                    new_packages[k] = v
        new_packages.update(self.packages)
        self.packages = new_packages

    def __repr__(self):
        return repr(self.packages)


def fetch(config, pkgdir):
    child_configs = []
    for i in config.packages.values():
        if hasattr(i, 'fetch'):
            mopack = i.fetch(pkgdir)
            if mopack:
                child_configs.append(Config([mopack], parent=config))
                fetch(child_configs[-1], pkgdir)
    config.add_children(child_configs)


def resolve(config, pkgdir):
    metadata, packages, batch_packages = {}, [], {}
    fetch(config, pkgdir)

    for i in config.packages.values():
        if hasattr(i, 'resolve_all'):
            batch_packages.setdefault(type(i), []).append(i)
        else:
            packages.append(i)

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


def _metadata_path(pkgdir):
    return os.path.join(pkgdir, metadata_filename)


def save_metadata(metadata, pkgdir):
    with open(_metadata_path(pkgdir), 'w') as f:
        json.dump(metadata, f)


def get_metadata(pkgdir):
    with open(_metadata_path(pkgdir)) as f:
        return json.load(f)
