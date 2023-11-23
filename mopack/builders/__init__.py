import os
import shutil
from pkg_resources import load_entry_point

from ..base_options import BaseOptions, OptionsHolder
from ..freezedried import GenericFreezeDried
from ..types import FieldValueError, wrap_field_error


def _get_builder_type(type, field='type'):
    try:
        return load_entry_point('mopack', 'mopack.builders', type)
    except ImportError:
        raise FieldValueError('unknown builder {!r}'.format(type), field)


@GenericFreezeDried.fields(skip={'name'})
class Builder(OptionsHolder):
    _options_type = 'builders'
    _type_field = 'type'
    _get_type = _get_builder_type

    Options = None

    def __init__(self, pkg):
        super().__init__(pkg._options)
        self.name = pkg.name

    @GenericFreezeDried.rehydrator
    def rehydrate(cls, config, *, name, **kwargs):
        result = super(Builder, cls).rehydrate(config, name=name, **kwargs)
        result.name = name
        return result

    def path_bases(self):
        return ('builddir',)

    def path_values(self, metadata):
        builddir = os.path.abspath(os.path.join(metadata.pkgdir, 'build',
                                                self.name))
        return {'builddir': builddir}

    def filter_linkage(self, linkage):
        return linkage

    def clean(self, metadata, pkg):
        path_values = pkg.path_values(metadata, builder=self)
        shutil.rmtree(path_values['builddir'], ignore_errors=True)

    def __repr__(self):
        return '<{}({!r})>'.format(type(self).__name__, self.name)


class BuilderOptions(GenericFreezeDried, BaseOptions):
    _type_field = 'type'

    @property
    def _context(self):
        return 'while adding options for {!r} builder'.format(self.type)

    @staticmethod
    def _get_type(type):
        return _get_builder_type(type).Options


def make_builder(pkg, config, *, field='build', **kwargs):
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
        return _get_builder_type(type, type_field)(pkg, **config, **kwargs)


def make_builder_options(type):
    opts = _get_builder_type(type).Options
    return opts() if opts else None
