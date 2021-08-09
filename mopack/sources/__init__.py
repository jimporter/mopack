import os
from pkg_resources import load_entry_point

from .. import types
from ..base_options import BaseOptions, OptionsHolder
from ..freezedried import FreezeDried
from ..iterutils import listify
from ..package_defaults import DefaultResolver
from ..path import Path
from ..placeholder import placeholder
from ..types import FieldValueError, try_load_config
from ..usage import Usage, make_usage


def _get_source_type(source, field='source'):
    try:
        return load_entry_point('mopack', 'mopack.sources', source)
    except ImportError:
        raise FieldValueError('unknown source {!r}'.format(source), field)


_submodule_dict = types.dict_shape({
    'names': types.one_of(types.list_of(types.string), types.constant('*'),
                          desc='a list of submodules'),
    'required': types.boolean,
}, desc='a list of submodules')


def submodules_type(field, value):
    if value is None:
        return None
    elif not isinstance(value, dict):
        value = {
            'names': value,
            'required': True,
        }
    return _submodule_dict(field, value)


@FreezeDried.fields(skip_compare={'parent', 'config_file', 'resolved'})
class Package(OptionsHolder):
    _options_type = 'sources'
    _default_genus = 'source'
    _type_field = 'source'
    _get_type = _get_source_type

    Options = None

    def __init__(self, name, *, deploy=True, parent=None,
                 _options, config_file):
        super().__init__(_options)
        self.name = name
        self.config_file = config_file
        self.resolved = False
        self.parent = parent.name if parent else None

        T = types.TypeCheck(locals(), self._expr_symbols)
        T.deploy(types.boolean, dest_field='should_deploy')

    @property
    def config_dir(self):
        return os.path.dirname(self.config_file)

    @property
    def needs_dependencies(self):
        return False

    @property
    def _expr_symbols(self):
        return dict(**self._options.expr_symbols,
                    cfgdir=placeholder(Path('', 'cfgdir')))

    def version(self, pkgdir):
        return self.explicit_version  # pragma: no cover

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

    def clean_pre(self, new_package, pkgdir, quiet=False):
        return False

    def clean_post(self, new_package, pkgdir, quiet=False):
        return False

    def clean_all(self, new_package, pkgdir, quiet=False):
        return (self.clean_pre(new_package, pkgdir, quiet),
                self.clean_post(new_package, pkgdir, quiet))

    def fetch(self, parent_config, pkgdir):
        pass  # pragma: no cover

    def get_usage(self, submodules, pkgdir):
        return self._get_usage(self._check_submodules(submodules), pkgdir)

    def __repr__(self):
        return '<{}({!r})>'.format(type(self).__name__, self.name)


@FreezeDried.fields(rehydrate={'usage': Usage})
class BinaryPackage(Package):
    def __init__(self, name, *, version=types.Unset, usage,
                 submodules=types.Unset, _options, _path_bases=(),
                 _usage_field='usage', **kwargs):
        # Currently, all binary packages are automatically-versioned. Perhaps
        # in the future, this will change.
        if version is not types.Unset:
            raise types.FieldKeyError((
                "{!r} package doesn't accept 'version' attribute; " +
                "version is determined automatically"
            ).format(self.source), 'version')

        super().__init__(name, _options=_options, **kwargs)

        symbols = self._expr_symbols
        package_default = DefaultResolver(self, symbols, name)
        T = types.TypeCheck(locals(), symbols)
        T.version(types.maybe(types.string), dest_field='explicit_version')
        T.submodules(package_default(submodules_type))

        self.usage = make_usage(name, usage, field=_usage_field,
                                submodules=self.submodules, _options=_options,
                                _path_bases=_path_bases)

    def _get_usage(self, submodules, pkgdir):
        return self.usage.get_usage(self, submodules, pkgdir, None, None)


class PackageOptions(FreezeDried, BaseOptions):
    _type_field = 'source'

    @property
    def _context(self):
        return 'while adding options for {!r} source'.format(self.source)

    @staticmethod
    def _get_type(source):
        return _get_source_type(source).Options


def make_package(name, config, **kwargs):
    fwd_config = config.copy()
    source = fwd_config.pop('source')
    return _get_source_type(source)(name, **fwd_config, **kwargs)


def try_make_package(name, config, **kwargs):
    context = 'while constructing package {!r}'.format(name)
    with try_load_config(config, context, config['source']):
        return make_package(name, config, **kwargs)


def make_package_options(source):
    opts = _get_source_type(source).Options
    return opts() if opts else None
