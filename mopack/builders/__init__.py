import importlib_metadata as metadata
import os
import shutil
from typing import Dict

from .. import types
from ..base_options import BaseOptions, OptionsHolder
from ..freezedried import GenericFreezeDried
from ..path import Path
from ..placeholder import MaybePlaceholderString


def _get_builder_type(type, field='type'):
    try:
        return metadata.entry_points(group='mopack.builders')[type].load()
    except KeyError:
        raise types.FieldValueError('unknown builder {!r}'.format(type), field)


@GenericFreezeDried.fields(rehydrate={
    'env': Dict[str, MaybePlaceholderString],
}, skip={'name'})
class Builder(OptionsHolder):
    _options_type = 'builders'
    _type_field = 'type'
    _get_type = _get_builder_type

    Options = None

    def __init__(self, pkg, *, env=None, _symbols):
        super().__init__(pkg._options)
        self.name = pkg.name

        T = types.TypeCheck(locals(), _symbols)
        T.env(types.maybe(types.dict_of(
            types.string, types.placeholder_string
        ), default={}))
        self._full_env = _symbols['env'].new_child(self.env)

    @GenericFreezeDried.rehydrator
    def rehydrate(cls, config, rehydrate_parent, *, name, _symbols, **kwargs):
        result = rehydrate_parent(Builder, config, name=name,
                                  _symbols=_symbols, **kwargs)
        result.name = name
        result._full_env = _symbols['env'].new_child(result.env)
        return result

    def path_bases(self):
        return ()

    def path_values(self, metadata, parent_values):
        return {}

    def filter_linkage(self, linkage):
        return linkage

    def clean(self, metadata, pkg):
        pass

    def build(self, metadata, pkg):
        pass

    def deploy(self, metadata, pkg):
        pass

    def __repr__(self):
        return '<{}({!r})>'.format(type(self).__name__, self.name)


@GenericFreezeDried.fields(rehydrate={'directory': Path})
class DirectoryBuilder(Builder):
    def __init__(self, pkg, *, directory=None, _symbols, **kwargs):
        super().__init__(pkg, _symbols=_symbols, **kwargs)
        if directory is None and _symbols.path_bases:
            directory = '$' + _symbols.path_bases[-1]
        T = types.TypeCheck(locals(), _symbols)
        T.directory(types.any_path('cfgdir'))


@GenericFreezeDried.fields(rehydrate={'child_builder': Builder})
class ConfiguringBuilder(DirectoryBuilder):
    def __init__(self, pkg, *, env=None, build=True, _symbols, _child_builder,
                 **kwargs):
        super().__init__(pkg, env=env, _symbols=_symbols, **kwargs)
        if build:
            _symbols = _symbols.augment(path_bases=self.path_bases())
            self.child_builder = _child_builder(
                pkg, env=env, _symbols=_symbols
            )
        else:
            self.child_builder = None

    def path_bases(self):
        return ('builddir',)

    def path_values(self, metadata, parent_values):
        builddir = os.path.abspath(os.path.join(metadata.pkgdir, 'build',
                                                self.name))
        return {'builddir': builddir}

    def clean(self, metadata, pkg):
        path_values = pkg.path_values(metadata)
        shutil.rmtree(path_values['builddir'], ignore_errors=True)

    def build(self, metadata, pkg):
        if self.child_builder:
            self.child_builder.build(metadata, pkg)

    def deploy(self, metadata, pkg):
        if self.child_builder:
            self.child_builder.deploy(metadata, pkg)


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

    with types.wrap_field_error(field, type):
        return _get_builder_type(type, type_field)(pkg, **config, **kwargs)


def make_builder_options(type):
    opts = _get_builder_type(type).Options
    return opts() if opts else None
