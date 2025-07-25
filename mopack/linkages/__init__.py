import importlib_metadata as metadata

from ..base_options import OptionsHolder
from ..freezedried import GenericFreezeDried
from ..types import FieldValueError, dependency_string, wrap_field_error


def _get_linkage_type(type, field='type'):
    try:
        return metadata.entry_points(group='mopack.linkages')[type].load()
    except KeyError:
        raise FieldValueError('unknown linkage {!r}'.format(type), field)


@GenericFreezeDried.fields(skip={'name', '_expr_symbols'})
class Linkage(OptionsHolder):
    _default_genus = 'linkage'
    _type_field = 'type'
    _get_type = _get_linkage_type

    def __init__(self, pkg, *, inherit_defaults=False, _symbols):
        super().__init__(pkg._options)
        self.name = pkg.name
        self._expr_symbols = _symbols

    @GenericFreezeDried.rehydrator
    def rehydrate(cls, config, rehydrate_parent, *, name, _symbols, **kwargs):
        result = rehydrate_parent(Linkage, config, name=name, **kwargs)
        result.name = name
        result._expr_symbols = _symbols
        return result

    def version(self, metadata, pkg):
        raise NotImplementedError('Linkage.version not implemented')

    def _linkage(self, submodules, **kwargs):
        return {'name': dependency_string(self.name, submodules),
                'type': self.type, **kwargs}

    def get_linkage(self, metadata, pkg, submodules):
        raise NotImplementedError('Linkage.get_linkage not implemented')

    def __repr__(self):
        return '<{}, {}>'.format(type(self).__name__, self.__dict__)


def make_linkage(pkg, config, *, field='linkage', **kwargs):
    if config is None:
        raise TypeError('linkage not specified')

    if isinstance(config, str):
        type_field = ()
        type = config
        config = {}
    else:
        type_field = 'type'
        config = config.copy()
        type = config.pop('type')

    if not config:
        config = {'inherit_defaults': True}

    with wrap_field_error(field, type):
        return _get_linkage_type(type, type_field)(pkg, **config, **kwargs)
