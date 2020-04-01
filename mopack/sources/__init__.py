from pkg_resources import load_entry_point


class Package:
    def __init__(self, name):
        self.name = name


def make_package(name, config):
    source = config.pop('source')
    try:
        source_type = load_entry_point('mopack', 'mopack.sources', source)
        return source_type(name, **config)
    except ImportError:
        raise ValueError('unknown source {!r}'.format(source))
