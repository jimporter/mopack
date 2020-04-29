from pkg_resources import load_entry_point

from ..freezedried import FreezeDried
from ..types import try_load_config


def _get_builder_type(type):
    try:
        return load_entry_point('mopack', 'mopack.builders', type)
    except ImportError:
        raise ValueError('unknown builder {!r}'.format(type))


class Builder(FreezeDried):
    _type_field = 'type'
    _get_type = _get_builder_type
    _skip_fields = ('global_options',)

    Options = None

    def __init__(self, name):
        self.name = name

    def set_options(self, options):
        self.global_options = options['builders'].get(self.type)

    def __repr__(self):
        return '<{}({!r})>'.format(type(self).__name__, self.name)


class BuilderOptions(FreezeDried):
    _type_field = 'type'

    @staticmethod
    def _get_type(type):
        return _get_builder_type(type).Options

    def accumulate(self, config):
        context = 'while adding options for {!r} builder'.format(self.type)
        with try_load_config(config, context):
            return self(**config)


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
