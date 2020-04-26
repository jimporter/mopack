from pkg_resources import load_entry_point

from ..freezedried import FreezeDried
from ..types import try_load_config


def _get_usage_type(type):
    try:
        return load_entry_point('mopack', 'mopack.usage', type)
    except ImportError:
        raise ValueError('unknown usage {!r}'.format(type))


class Usage(FreezeDried):
    _type_field = 'type'
    _get_type = _get_usage_type

    def _usage(self, **kwargs):
        return dict(type=self.type, **kwargs)

    def __repr__(self):
        return '<{}>'.format(type(self).__name__)


def make_usage(config):
    if isinstance(config, str):
        type = config
        config = {}
    else:
        config = config.copy()
        type = config.pop('type')

    context = 'while constructing usage {!r}'.format(type)
    with try_load_config(config, context):
        return _get_usage_type(type)(**config)
