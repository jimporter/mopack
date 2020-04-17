from pkg_resources import load_entry_point
from yaml.error import MarkedYAMLError

from ..freezedried import FreezeDried
from ..yaml_tools import MarkedDict
from ..types import FieldError


def _get_builder_type(type):
    try:
        return load_entry_point('mopack', 'mopack.builders', type)
    except ImportError:
        raise ValueError('unknown builder {!r}'.format(type))


class Builder(FreezeDried):
    _type_field = 'type'
    _get_type = _get_builder_type

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<{}({!r})>'.format(type(self).__name__, self.name)


def make_builder(name, config, **kwargs):
    if isinstance(config, str):
        type = config
        config = {}
    else:
        config = config.copy()
        type = config.pop('type')

    try:
        return _get_builder_type(type)(name, **config, **kwargs)
    except TypeError as e:
        if not isinstance(config, MarkedDict):
            raise

        context = 'while constructing builder {!r}'.format(name)
        mark = (config.marks[e.field] if isinstance(e, FieldError)
                else config.mark)
        raise MarkedYAMLError(context, config.mark, str(e), mark)
