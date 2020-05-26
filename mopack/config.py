import os
from itertools import chain

from .builders import make_builder_options
from .freezedried import FreezeDried
from .options import BaseOptions
from .sources import make_package, make_package_options
from .types import Unset
from .yaml_tools import load_file, MarkedDict, SafeLineLoader


class _PlaceholderPackage:
    def __repr__(self):
        return '<PlaceholderPackage>'


PlaceholderPackage = _PlaceholderPackage()


class GeneralOptions(FreezeDried, BaseOptions):
    _context = 'while adding general options'

    def __init__(self):
        self.target_platform = Unset

    def __call__(self, *, target_platform=Unset, **kwargs):
        if self.target_platform is Unset:
            self.target_platform = target_platform


class BaseConfig:
    _option_kinds = ('builders', 'sources')

    @classmethod
    def default_options(cls):
        # This function just happens to work for both "pending" options as we
        # parse each config file, as well as being the default state for
        # finalized options.
        return {i: {} for i in cls._option_kinds}

    def __init__(self):
        self._options = self.default_options()
        self.packages = {}

    def _accumulate_config(self, filename):
        filename = os.path.abspath(filename)
        with load_file(filename, Loader=SafeLineLoader) as next_config:
            if next_config:
                for k, v in next_config.items():
                    fn = '_process_{}'.format(k)
                    if hasattr(self, fn):
                        getattr(self, fn)(filename, v)

    def _process_packages(self, filename, data):
        if not data:
            return
        for k, v in data.items():
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

    def _process_options(self, filename, data):
        if not data:
            return
        for kind in self._option_kinds:
            if kind in data:
                for k, v in data[kind].items():
                    if v is None:
                        v = MarkedDict(data[kind].marks[k])
                    v.update(config_file=filename, child_config=self.child)
                    self._options[kind].setdefault(k, []).append(v)

    def _in_parent(self, name):
        # We don't have a parent, so this is always false!
        return False

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

            for kind in self._option_kinds:
                if kind in i._options:
                    for k, v in i._options[kind].items():
                        self._options[kind].setdefault(k, []).extend(v)
        new_packages.update(self.packages)
        self.packages = new_packages


class Config(BaseConfig):
    child = False

    @classmethod
    def default_options(cls):
        # As above, this function works for both "pending" options and
        # finalized options.
        result = super().default_options()
        result['general'] = GeneralOptions()
        return result

    def __init__(self, filenames, options=None):
        super().__init__()
        self._process_options('<command-line>', options or {})
        for f in reversed(filenames):
            self._accumulate_config(f)

    def _process_options(self, filename, data):
        super()._process_options(filename, data)

        if data:
            general = data.copy()
            for i in self._option_kinds:
                general.pop(i, None)
            if general:
                self._options['general'].accumulate(general)

    def finalize(self):
        def make_options(kinds, make):
            for i in kinds:
                opts = make(i)
                if opts:
                    yield i, opts

        sources = {pkg.source: True for pkg in self.packages.values()}
        builders = {i: True for i in chain.from_iterable(
            pkg.builder_types for pkg in self.packages.values()
        )}

        self.options = {
            'general': self._options['general'],
            'sources': dict(make_options(sources, make_package_options)),
            'builders': dict(make_options(builders, make_builder_options)),
        }

        for kind in self._option_kinds:
            for name, cfgs in self._options[kind].items():
                if name in self.options[kind]:
                    for cfg in cfgs:
                        final = cfg.pop('final', False)
                        self.options[kind][name].accumulate(cfg)
                        if final:
                            break
        del self._options

        for pkg in self.packages.values():
            pkg.set_options(self.options)


class ChildConfig(BaseConfig):
    child = True

    def __init__(self, filenames, parent):
        super().__init__()
        self.parent = parent
        for f in reversed(filenames):
            self._accumulate_config(f)

    def _in_parent(self, name):
        return name in self.parent.packages or self.parent._in_parent(name)

    def _process_self(self, filename, data):
        self.submodules = data.get('submodules')
        self.build = data.get('build')
        self.usage = data.get('usage')
