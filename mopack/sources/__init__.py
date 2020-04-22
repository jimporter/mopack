import os
from pkg_resources import load_entry_point
from yaml.error import MarkedYAMLError

from ..freezedried import FreezeDried
from ..yaml_tools import MarkedDict
from ..types import FieldError


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

    def clean_pre(self, pkgdir, new_package):
        return False

    def clean_post(self, pkgdir, new_package):
        return False

    def clean_all(self, pkgdir, new_package):
        return (self.clean_pre(pkgdir, new_package),
                self.clean_post(pkgdir, new_package))

    def fetch(self, pkgdir, parent_config):
        pass

    def _resolved_metadata(self, usage):
        return {'config': self.dehydrate(), 'usage': usage}

    @staticmethod
    def _resolved_metadata_all(packages, usage):
        return [p._resolved_metadata(u) for p, u in zip(packages, usage)]

    def __repr__(self):
        return '<{}({!r})>'.format(type(self).__name__, self.name)


def make_package(name, config):
    config = config.copy()
    source = config.pop('source')

    try:
        return _get_source_type(source)(name, **config)
    except TypeError as e:
        if not isinstance(config, MarkedDict):
            raise

        context = 'while constructing package {!r}'.format(name)
        mark = (config.marks[e.field] if isinstance(e, FieldError)
                else config.mark)
        raise MarkedYAMLError(context, config.mark, str(e), mark)
