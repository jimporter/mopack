from pkg_resources import load_entry_point

from ..base_options import OptionsHolder
from ..path import Path
from ..placeholder import placeholder
from ..types import FieldValueError, wrap_field_error


class _SubmodulePlaceholder:
    pass


submodule_placeholder = _SubmodulePlaceholder()


def _get_usage_type(type, field='type'):
    try:
        return load_entry_point('mopack', 'mopack.usage', type)
    except ImportError:
        raise FieldValueError('unknown usage {!r}'.format(type), field)


class Usage(OptionsHolder):
    _default_genus = 'usage'
    _type_field = 'type'
    _get_type = _get_usage_type

    def __init__(self, *, _options):
        super().__init__(_options)

    def _expr_symbols(self, path_bases):
        path_vars = {i: placeholder(Path(i, '')) for i in path_bases}
        return dict(**self._options.expr_symbols, **path_vars)

    def _preferred_base(self, preferred, path_bases):
        if preferred in path_bases:
            return preferred
        elif len(path_bases) > 0:
            return path_bases[0]
        else:
            return None

    def _usage(self, *, type=None, **kwargs):
        if type is None:
            type = self.type
        return dict(type=type, **kwargs)

    def __repr__(self):
        return '<{}, {}>'.format(type(self).__name__, self.__dict__)


def make_usage(name, config, *, field='usage', **kwargs):
    if config is None:
        raise TypeError('usage not specified')

    if isinstance(config, str):
        with wrap_field_error(field, config):
            return _get_usage_type(config, ())(name, **kwargs)
    else:
        fwd_config = config.copy()
        type = fwd_config.pop('type')
        with wrap_field_error(field, type):
            return _get_usage_type(type)(name, **fwd_config, **kwargs)
