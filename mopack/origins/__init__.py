import importlib_metadata as metadata
import os
import warnings

from .. import types
from ..base_options import BaseOptions, OptionsHolder
from ..freezedried import GenericFreezeDried
from ..iterutils import ismapping, listify
from ..linkages import Linkage, make_linkage
from ..package_defaults import DefaultResolver
from ..types import (FieldKeyError, FieldValueError, try_load_config,
                     wrap_field_error)


def _get_origin_type(origin, field='origin'):
    try:
        return metadata.entry_points(group='mopack.origins')[origin].load()
    except KeyError:
        raise FieldValueError('unknown origin {!r}'.format(origin), field)


_submodule_dict = types.dict_shape({
    'names': types.one_of(types.list_of(types.string), types.constant('*'),
                          desc='a list of submodules'),
    'required': types.boolean,
}, desc='a list of submodules')


def submodules_type(field, value):
    if value is None:
        return None
    elif not ismapping(value):
        value = {
            'names': value,
            'required': True,
        }
    return _submodule_dict(field, value)


@GenericFreezeDried.fields(rehydrate={'linkage': Linkage},
                           skip_compare={'parent', 'config_file', 'resolved'})
class Package(OptionsHolder):
    _options_type = 'origins'
    _default_genus = 'origin'
    _type_field = 'origin'
    _get_type = _get_origin_type

    Options = None

    def __init__(self, name, *, deploy=True, parent=None,
                 inherit_defaults=False, _options, config_file):
        super().__init__(_options)
        self.name = name
        self.config_file = config_file
        self.resolved = False
        self.parent = parent.name if parent else None

        self._expr_symbols = self._options.expr_symbols
        if self.config_file:
            self._expr_symbols = self._expr_symbols.augment(
                path_bases=['cfgdir']
            )

        T = types.TypeCheck(locals(), self._expr_symbols)
        T.deploy(types.boolean, dest_field='should_deploy')

    @GenericFreezeDried.rehydrator
    def rehydrate(cls, config, rehydrate_parent, *, _after_rehydrate=None,
                  **kwargs):
        linkage_cfg = config.pop('linkage')

        pkg = rehydrate_parent(Package, config, **kwargs)
        pkg._expr_symbols = pkg._options.expr_symbols.augment(
            path_bases=['cfgdir']
        )

        if _after_rehydrate:
            pkg = _after_rehydrate(pkg)

        pkg.linkage = Linkage.rehydrate(
            linkage_cfg, name=config['name'],
            _symbols=pkg._linkage_expr_symbols, **kwargs
        )
        return pkg

    @property
    def _linkage_expr_symbols(self):
        return self._options.expr_symbols

    @property
    def config_dir(self):
        return os.path.dirname(self.config_file)

    @property
    def needs_dependencies(self):
        return False

    def guessed_version(self, metadata):
        return None

    def version(self, metadata):
        return self.linkage.version(metadata, self)

    def _check_submodules(self, wanted_submodules):
        if self.submodules:
            if self.submodules['required'] and not wanted_submodules:
                raise ValueError('package {!r} requires submodules'
                                 .format(self.name))

            wanted_submodules = listify(wanted_submodules)
            if self.submodules['names'] != '*':
                for i in wanted_submodules:
                    if i not in self.submodules['names']:
                        raise ValueError(
                            'unrecognized submodule {!r} for package {!r}'
                            .format(i, self.name)
                        )
            return wanted_submodules
        elif wanted_submodules:
            raise ValueError('package {!r} has no submodules'
                             .format(self.name))
        return None

    @property
    def builder_types(self):
        return []

    def path_values(self, metadata):
        try:
            return {'cfgdir': self.config_dir}
        except TypeError:
            return {}

    def clean_pre(self, metadata, new_package, quiet=False):
        return False

    def clean_post(self, metadata, new_package, quiet=False):
        return False

    def clean_all(self, metadata, new_package, quiet=False):
        return (self.clean_pre(metadata, new_package, quiet),
                self.clean_post(metadata, new_package, quiet))

    def fetch(self, metadata, parent_config):
        pass  # pragma: no cover

    def resolve(self, metadata):
        self.resolved = True

    def deploy(self, metadata):
        pass

    def get_linkage(self, metadata, submodules):
        return self.linkage.get_linkage(
            metadata, self, self._check_submodules(submodules)
        )

    def __repr__(self):
        return '<{}({!r})>'.format(type(self).__name__, self.name)


class BatchPackage(Package):
    def resolve(self, metadata):
        raise NotImplementedError()

    def deploy(self, metadata):
        raise NotImplementedError()

    @classmethod
    def resolve_all(cls, metadata, packages):
        for i in packages:
            i.resolved = True

    @staticmethod
    def deploy_all(metadata, packages):
        pass


class BinaryPackage(Package):
    # TODO: Remove `usage` after v0.2 is released.
    def __init__(self, name, *, submodules=types.Unset, linkage=types.Unset,
                 usage=types.Unset, inherit_defaults=False, _options,
                 _linkage_field='linkage', **kwargs):
        if linkage is types.Unset and usage is not types.Unset:
            warnings.warn(types.FieldKeyWarning(
                '`usage` is deprecated; use `linkage` instead', 'usage'
            ))
            linkage = usage
        if linkage is types.Unset:
            raise TypeError('missing `linkage`')

        super().__init__(name, inherit_defaults=inherit_defaults,
                         _options=_options, **kwargs)

        symbols = self._expr_symbols
        pkg_default = DefaultResolver(self, symbols, inherit_defaults, name)
        T = types.TypeCheck(locals(), symbols)
        T.submodules(pkg_default(submodules_type))

        self.linkage = make_linkage(self, linkage, field=_linkage_field,
                                    _symbols=self._linkage_expr_symbols)


class PackageOptions(GenericFreezeDried, BaseOptions):
    _type_field = 'origin'

    @property
    def _context(self):
        return 'while adding options for {!r} origin'.format(self.origin)

    @staticmethod
    def _get_type(origin):
        return _get_origin_type(origin).Options


def make_package(name, config, **kwargs):
    # config_file should always be specified in kwargs.
    if 'config_file' in config:
        raise FieldKeyError('config_file is reserved', 'config_file')

    config = config.copy()
    origin = config.pop('origin')

    if not config:
        config = {'inherit_defaults': True}

    return _get_origin_type(origin)(name, **config, **kwargs)


def try_make_package(name, config, **kwargs):
    context = 'while constructing package {!r}'.format(name)
    with try_load_config(config, context):
        if 'origin' not in config:
            raise FieldKeyError("missing required field 'origin'", None)
        with wrap_field_error(None, config['origin']):
            return make_package(name, config, **kwargs)


def make_package_options(origin):
    opts = _get_origin_type(origin).Options
    return opts() if opts else None
