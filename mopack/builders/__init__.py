import os
from pkg_resources import load_entry_point

from ..freezedried import FreezeDried
from ..options import BaseOptions, OptionsSet
from ..package_defaults import finalize_defaults
from ..types import try_load_config
from ..usage import Usage, make_usage


def _get_builder_type(type):
    try:
        return load_entry_point('mopack', 'mopack.builders', type)
    except ImportError:
        raise ValueError('unknown builder {!r}'.format(type))


class Builder(FreezeDried):
    _type_field = 'type'
    _get_type = _get_builder_type
    _skip_fields = _skip_compare_fields = ('_options',)
    _rehydrate_fields = {'usage': Usage}

    Options = None

    def __init__(self, name, *, usage, submodules):
        self.name = name
        self.usage = make_usage(name, usage, submodules=submodules)

    def _builddir(self, pkgdir):
        return os.path.abspath(os.path.join(pkgdir, 'build', self.name))

    def set_options(self, options):
        self.usage.set_options(options)
        self._options = OptionsSet(options['common'],
                                   options['builders'].get(self.type))
        finalize_defaults(self._options, self)

    def get_usage(self, pkgdir, submodules, srcdir):
        return self.usage.get_usage(submodules, srcdir, self._builddir(pkgdir))

    def __repr__(self):
        return '<{}({!r})>'.format(type(self).__name__, self.name)


class BuilderOptions(FreezeDried, BaseOptions):
    _type_field = 'type'

    @property
    def _context(self):
        return 'while adding options for {!r} builder'.format(self.type)

    @staticmethod
    def _get_type(type):
        return _get_builder_type(type).Options


def make_builder(name, config, **kwargs):
    if isinstance(config, str):
        type = config
        config = {}
    else:
        config = config.copy()
        type = config.pop('type')

    context = 'while constructing builder {!r}'.format(name)
    with try_load_config(config, context, type):
        return _get_builder_type(type)(name, **config, **kwargs)


def make_builder_options(type):
    opts = _get_builder_type(type).Options
    return opts() if opts else None
