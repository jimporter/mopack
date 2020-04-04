import os
from pkg_resources import load_entry_point


class Package:
    def __init__(self, name, _config_file):
        self.name = name
        self.config_file = _config_file

    @property
    def config_dir(self):
        return os.path.dirname(self.config_file)

    def __repr__(self):
        return '<{}({!r})>'.format(type(self).__name__, self.name)


def make_package(name, config):
    source = config.pop('source')
    try:
        source_type = load_entry_point('mopack', 'mopack.sources', source)
        return source_type(name, **config)
    except ImportError:
        raise ValueError('unknown source {!r}'.format(source))
