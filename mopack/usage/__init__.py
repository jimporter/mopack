from pkg_resources import load_entry_point

from ..freezedried import FreezeDried
from ..options import OptionsSet
from ..package_defaults import finalize_defaults, package_default
from ..types import try_load_config


def _get_usage_type(type):
    try:
        return load_entry_point('mopack', 'mopack.usage', type)
    except ImportError:
        raise ValueError('unknown usage {!r}'.format(type))


class Usage(FreezeDried):
    _type_field = 'type'
    _get_type = _get_usage_type
    _skip_fields = _skip_compare_fields = ('_options',)

    def _package_default(self, other, name, field=None, default=None):
        return package_default(other, name, 'usage', self.type, field, default)

    def set_options(self, options):
        self._options = OptionsSet(options['common'], None)
        finalize_defaults(self._options, self)

    def _usage(self, **kwargs):
        return dict(type=self.type, **kwargs)

    def __repr__(self):
        return '<{}, {}>'.format(type(self).__name__, self.__dict__)


def make_usage(name, config, **kwargs):
    if isinstance(config, str):
        type = config
        config = {}
    else:
        config = config.copy()
        type = config.pop('type')

    context = 'while constructing usage {!r}'.format(type)
    with try_load_config(config, context):
        return _get_usage_type(type)(name, **config, **kwargs)
