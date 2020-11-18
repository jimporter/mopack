from pkg_resources import load_entry_point

from ..freezedried import FreezeDried
from ..options import OptionsSet
from ..package_defaults import finalize_defaults, package_default
from ..types import FieldError, wrap_field_error


def _get_usage_type(type, field='type'):
    try:
        return load_entry_point('mopack', 'mopack.usage', type)
    except ImportError:
        raise FieldError('unknown usage {!r}'.format(type), field)


class Usage(FreezeDried):
    _type_field = 'type'
    _get_type = _get_usage_type
    _skip_fields = _skip_compare_fields = ('_options',)

    def _package_default(self, other, name, field=None, default=None):
        return package_default(other, name, 'usage', self.type, field, default)

    def set_options(self, options):
        self._options = OptionsSet(options['common'], None)
        finalize_defaults(options['common'], self)

    def _usage(self, **kwargs):
        return dict(type=self.type, **kwargs)

    def __repr__(self):
        return '<{}, {}>'.format(type(self).__name__, self.__dict__)


def make_usage(name, config, *, field='usage', **kwargs):
    if isinstance(config, str):
        with wrap_field_error(field, config):
            return _get_usage_type(config, ())(name, **kwargs)
    else:
        fwd_config = config.copy()
        type = fwd_config.pop('type')
        with wrap_field_error(field, type):
            return _get_usage_type(type)(name, **fwd_config, **kwargs)
