import os
import shutil
from pkg_resources import load_entry_point

from ..base_options import BaseOptions, OptionsHolder
from ..freezedried import FreezeDried
from ..path import Path
from ..placeholder import placeholder
from ..types import FieldValueError, wrap_field_error
from ..usage import make_usage, Usage


def _get_builder_type(type, field='type'):
    try:
        return load_entry_point('mopack', 'mopack.builders', type)
    except ImportError:
        raise FieldValueError('unknown builder {!r}'.format(type), field)


@FreezeDried.fields(rehydrate={'usage': Usage})
class Builder(OptionsHolder):
    _options_type = 'builders'
    _type_field = 'type'
    _get_type = _get_builder_type

    Options = None

    def __init__(self, name, *, _options):
        super().__init__(_options)
        self.name = name

    def set_usage(self, usage, **kwargs):
        # We set the usage separately since, even though the builder owns the
        # usage, they're siblings in the mopack.yml file. This would confuse
        # the FieldError wrapping, making errors in usage appear as if they
        # were "inside" the builder. Thus, the separate `set_usage` call.
        self.usage = make_usage(self.name, usage, _options=self._options,
                                _path_bases=self._path_bases, **kwargs)

    @property
    def _expr_symbols(self):
        path_vars = {i: placeholder(Path('', i)) for i in self._path_bases}
        return dict(**self._options.expr_symbols, **path_vars)

    def _builddir(self, pkgdir):
        return os.path.abspath(os.path.join(pkgdir, 'build', self.name))

    def clean(self, pkgdir):
        shutil.rmtree(self._builddir(pkgdir), ignore_errors=True)

    def __repr__(self):
        return '<{}({!r})>'.format(type(self).__name__, self.name)


class BuilderOptions(FreezeDried, BaseOptions):
    _type_field = 'type'

    @property
    def _context(self):
        return 'while adding options for {!r} builder'.format(self.type)

    @staticmethod
    def _get_type(type):
        return _get_builder_type(type).Options


def make_builder(name, config, *, field='build', **kwargs):
    if config is None:
        raise TypeError('builder not specified')

    if isinstance(config, str):
        type_field = ()
        type = config
        config = {}
    else:
        type_field = 'type'
        config = config.copy()
        type = config.pop('type')

    with wrap_field_error(field, type):
        return _get_builder_type(type, type_field)(name, **config, **kwargs)


def make_builder_options(type):
    opts = _get_builder_type(type).Options
    return opts() if opts else None
