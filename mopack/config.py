import os

from .yaml_tools import load_file, SafeLineLoader
from .sources import make_package


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
        with load_file(filename, Loader=SafeLineLoader) as next_config:
            for k, v in next_config['packages'].items():
                if k in self.packages:
                    continue
                v['config_file'] = filename

                # If a parent package has already defined this package,
                # just store a placeholder to track it. Otherwise, make the
                # real package object.
                self.packages[k] = (
                    PlaceholderPackage if self._in_parent(k)
                    else make_package(k, v)
                )

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
