import os
from pkg_resources import load_entry_point

from ..base_options import BaseOptions, OptionsSet
from ..freezedried import FreezeDried
from ..types import FieldError, wrap_field_error
from ..usage import Usage


def _get_builder_type(type, field='type'):
    try:
        return load_entry_point('mopack', 'mopack.builders', type)
    except ImportError:
        raise FieldError('unknown builder {!r}'.format(type), field)


@FreezeDried.fields(rehydrate={'usage': Usage}, skip={'_options'},
                    skip_compare={'_options'})
class Builder(FreezeDried):
    _type_field = 'type'
    _get_type = _get_builder_type

    Options = None

    def __init__(self, name, *, usage):
        self.name = name
        self.usage = usage

    def _builddir(self, pkgdir):
        return os.path.abspath(os.path.join(pkgdir, 'build', self.name))

    def set_options(self, options):
        self.usage.set_options(options)
        self._options = OptionsSet(options.common,
                                   options.builders.get(self.type))

    def get_usage(self, pkgdir, submodules, srcdir):
        return self.usage.get_usage(submodules, srcdir, self._builddir(pkgdir))

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
    if isinstance(config, str):
        with wrap_field_error(field, config):
            return _get_builder_type(config, ())(name, **kwargs)
    else:
        fwd_config = config.copy()
        type = fwd_config.pop('type')
        with wrap_field_error(field, type):
            return _get_builder_type(type)(name, **fwd_config, **kwargs)


def make_builder_options(type):
    opts = _get_builder_type(type).Options
    return opts() if opts else None
