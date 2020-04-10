from pkg_resources import load_entry_point

from ..freezedried import FreezeDried


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


def make_builder(name, config):
    if isinstance(config, str):
        type = config
        config = {}
    else:
        config = config.copy()
        type = config.pop('type')

    return _get_builder_type(type)(name, **config)
