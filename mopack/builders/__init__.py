from pkg_resources import load_entry_point


def make_builder(name, config):
    if isinstance(config, str):
        kind = config
        config = {}
    else:
        kind = config.pop('type')

    try:
        builder_type = load_entry_point('mopack', 'mopack.builders', kind)
        return builder_type(name, **config)
    except ImportError:
        raise ValueError('unknown builder {!r}'.format(kind))
