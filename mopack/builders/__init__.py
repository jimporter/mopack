from pkg_resources import load_entry_point

from ..freezedried import FreezeDried
from ..options import BaseOptions
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
    _skip_fields = ('global_options',)
    _rehydrate_fields = {'usage': Usage}

    Options = None

    def __init__(self, name, *, usage):
        self.name = name
        self.usage = (usage if isinstance(usage, Usage) else
                      make_usage(name, usage))

    def set_options(self, options):
        self.global_options = options['builders'].get(self.type)
        self.usage.set_options(options)

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
    with try_load_config(config, context):
        return _get_builder_type(type)(name, **config, **kwargs)


def make_builder_options(type):
    opts = _get_builder_type(type).Options
    return opts() if opts else None
