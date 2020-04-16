from pkg_resources import load_entry_point
from yaml.error import MarkedYAMLError

from ..freezedried import FreezeDried
from ..yaml_loader import MarkedDict
from ..types import FieldError


def _get_usage_type(type):
    try:
        return load_entry_point('mopack', 'mopack.usage', type)
    except ImportError:
        raise ValueError('unknown usage {!r}'.format(type))


class Usage(FreezeDried):
    _type_field = 'type'
    _get_type = _get_usage_type

    def _usage(self, **kwargs):
        kwargs['type'] = self.type
        return kwargs

    def __repr__(self):
        return '<{}>'.format(type(self).__name__)


def make_usage(config):
    if isinstance(config, str):
        type = config
        config = {}
    else:
        config = config.copy()
        type = config.pop('type')

    try:
        return _get_usage_type(type)(**config)
    except TypeError as e:
        if not isinstance(config, MarkedDict):
            raise

        context = 'while constructing usage {!r}'.format(type)
        mark = (config.marks[e.field] if isinstance(e, FieldError)
                else config.mark)
        raise MarkedYAMLError(context, config.mark, str(e), mark)
