import os
from itertools import chain
from yaml.error import MarkedYAMLError

from . import expression as expr
from .builders import make_builder_options
from .freezedried import FreezeDried
from .iterutils import isiterable
from .options import BaseOptions
from .platforms import platform_name
from .sources import make_package, make_package_options
from .types import Unset
from .yaml_tools import load_file, to_parse_error, MarkedDict, SafeLineLoader


class _PlaceholderPackage:
    def __repr__(self):
        return '<PlaceholderPackage>'


PlaceholderPackage = _PlaceholderPackage()


class CommonOptions(FreezeDried, BaseOptions):
    _context = 'while adding common options'
    type = 'common'

    def __init__(self):
        self.target_platform = Unset
        self.env = {}

    def __call__(self, *, target_platform=Unset, env=None, **kwargs):
        if self.target_platform is Unset:
            self.target_platform = target_platform
        if env:
            for k, v in env.items():
                if k not in self.env:
                    self.env[k] = v

    def finalize(self):
        self(target_platform=platform_name(), env=os.environ)


class BaseConfig:
    _option_kinds = ('builders', 'sources')

    @classmethod
    def default_options(cls, pending=False):
        # This function returns the same data for both "pending" options as we
        # parse each config file, as well as being the default state for
        # finalized options.
        return {i: {} for i in cls._option_kinds}

    def __init__(self):
        self._options = self.default_options(pending=True)
        self._pending_packages = {}

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

        for name, cfgs in data.items():
            # If a parent package has already defined this package,
            # just store a placeholder to track it. Otherwise, make the
            # real package object.
            if self._in_parent(name):
                if name not in self._pending_packages:
                    self._pending_packages[name] = PlaceholderPackage
                continue

            if name not in self._pending_packages:
                self._pending_packages[name] = []

            if isiterable(cfgs):
                for i, cfg in enumerate(cfgs):
                    if i < len(cfgs) - 1 and 'if' not in cfg:
                        ctx = 'while constructing package {!r}'.format(name)
                        msg = ('package config has no `if` field, but is ' +
                               'not last entry of list')
                        raise MarkedYAMLError(ctx, cfgs.mark, msg, cfg.mark)
                    cfg['config_file'] = filename
                    self._pending_packages[name].append(cfg)
            else:
                cfgs['config_file'] = filename
                self._pending_packages[name].append(cfgs)

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

    def _finalize_packages(self, symbols):
        self.packages = {}
        for name, cfgs in self._pending_packages.items():
            if cfgs is PlaceholderPackage:
                self.packages[name] = cfgs
                continue

            for cfg in cfgs:
                with to_parse_error(cfg['config_file']):
                    if self._evaluate(symbols, cfg, 'if'):
                        self.packages[name] = make_package(name, cfg)
                        break
        del self._pending_packages

    @staticmethod
    def _evaluate(symbols, data, key):
        try:
            mark = data.value_marks.get(key)
            expression = data.pop(key, True)
            if isinstance(expression, bool):
                return expression
            return expr.evaluate(symbols, expression)
        except expr.ParseException as e:
            raise expr.to_yaml_error(e, data.mark, mark)

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
    def default_options(cls, pending=False):
        result = super().default_options(pending)
        result['common'] = CommonOptions()
        if not pending:
            result['common'].finalize()
        return result

    def __init__(self, filenames, options=None):
        super().__init__()
        self._process_options('<command-line>', options or {})
        for f in reversed(filenames):
            self._accumulate_config(f)
        self._options['common'].finalize()
        self._expr_symbols = {
            'host_platform': platform_name(),
            'target_platform': self._options['common'].target_platform
        }
        self._finalize_packages(self._expr_symbols)

    def _process_options(self, filename, data):
        super()._process_options(filename, data)

        if data:
            common = data.copy()
            for i in self._option_kinds:
                common.pop(i, None)
            if common:
                self._options['common'].accumulate(common)

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
            'common': self._options['common'],
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
        self._finalize_packages(self._expr_symbols)

    @property
    def _expr_symbols(self):
        parent = self.parent
        while hasattr(parent, 'parent'):
            parent = self.parent
        return parent._expr_symbols

    def _in_parent(self, name):
        return name in self.parent.packages or self.parent._in_parent(name)

    def _process_self(self, filename, data):
        self.submodules = data.get('submodules')
        self.build = data.get('build')
        self.usage = data.get('usage')
