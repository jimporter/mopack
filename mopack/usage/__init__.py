from pkg_resources import load_entry_point

from ..base_options import OptionsSet
from ..freezedried import FreezeDried
from ..types import FieldError, wrap_field_error


def _get_usage_type(type, field='type'):
    try:
        return load_entry_point('mopack', 'mopack.usage', type)
    except ImportError:
        raise FieldError('unknown usage {!r}'.format(type), field)


@FreezeDried.fields(skip={'_options'}, skip_compare={'_options'})
class Usage(FreezeDried):
    _default_genus = 'usage'
    _type_field = 'type'
    _get_type = _get_usage_type

    def set_options(self, options):
        self._options = OptionsSet(options.common, None)

    def _usage(self, *, type=None, **kwargs):
        if type is None:
            type = self.type
        return dict(type=type, **kwargs)

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
