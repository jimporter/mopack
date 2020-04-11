import os
from pkg_resources import load_entry_point

from ..freezedried import FreezeDried


def _get_source_type(source):
    try:
        return load_entry_point('mopack', 'mopack.sources', source)
    except ImportError:
        raise ValueError('unknown source {!r}'.format(source))


class Package(FreezeDried):
    _type_field = 'source'
    _get_type = _get_source_type
    _skip_compare_fields = ('config_file',)

    def __init__(self, name, *, config_file):
        self.name = name
        self.config_file = config_file

    @property
    def config_dir(self):
        return os.path.dirname(self.config_file)

    def clean_needed(self, pkgdir, new_package):
        return False

    def fetch(self, pkgdir):
        pass

    def _resolved_metadata(self, usage):
        return {'config': self.dehydrate(), 'usage': usage}

    @staticmethod
    def _resolved_metadata_all(packages, usage):
        return [i._resolved_metadata(usage) for i in packages]

    def __repr__(self):
        return '<{}({!r})>'.format(type(self).__name__, self.name)


def make_package(name, config):
    config = config.copy()
    source = config.pop('source')
    return _get_source_type(source)(name, **config)
