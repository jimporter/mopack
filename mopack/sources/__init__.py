import os
from pkg_resources import load_entry_point

from .. import types
from ..freezedried import FreezeDried
from ..iterutils import listify
from ..options import BaseOptions, OptionsSet
from ..package_defaults import package_default, finalize_defaults
from ..types import try_load_config
from ..usage import Usage, make_usage


def _get_source_type(source):
    try:
        return load_entry_point('mopack', 'mopack.sources', source)
    except ImportError:
        raise ValueError('unknown source {!r}'.format(source))


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


class Package(FreezeDried):
    _type_field = 'source'
    _get_type = _get_source_type
    _skip_fields = ('_options',)
    _skip_compare_fields = ('config_file', '_options')

    Options = None

    def __init__(self, name, *, config_file):
        self.name = name
        self.config_file = config_file

    @property
    def config_dir(self):
        return os.path.dirname(self.config_file)

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

    def set_options(self, options):
        self._options = OptionsSet(options['common'],
                                   options['sources'].get(self.source))
        finalize_defaults(self._options, self)

    def clean_pre(self, pkgdir, new_package):
        return False

    def clean_post(self, pkgdir, new_package):
        return False

    def clean_all(self, pkgdir, new_package):
        return (self.clean_pre(pkgdir, new_package),
                self.clean_post(pkgdir, new_package))

    def fetch(self, pkgdir, parent_config):
        pass

    def get_usage(self, pkgdir, submodules):
        return self._get_usage(pkgdir, self._check_submodules(submodules))

    def __repr__(self):
        return '<{}({!r})>'.format(type(self).__name__, self.name)


class BinaryPackage(Package):
    _rehydrate_fields = {'usage': Usage}

    def __init__(self, name, *, usage, submodules=types.Unset, **kwargs):
        super().__init__(name, **kwargs)
        self.submodules = package_default(submodules_type, name)(
            'submodules', submodules
        )
        self.usage = make_usage(name, usage, submodules=self.submodules)

    def set_options(self, options):
        self.usage.set_options(options)
        super().set_options(options)

    def _get_usage(self, pkgdir, submodules):
        return self.usage.get_usage(submodules, None, None)


class PackageOptions(FreezeDried, BaseOptions):
    _type_field = 'source'

    @property
    def _context(self):
        return 'while adding options for {!r} source'.format(self.source)

    @staticmethod
    def _get_type(source):
        return _get_source_type(source).Options


def make_package(name, config):
    config = config.copy()
    source = config.pop('source')

    context = 'while constructing package {!r}'.format(name)
    with try_load_config(config, context):
        return _get_source_type(source)(name, **config)


def make_package_options(source):
    opts = _get_source_type(source).Options
    return opts() if opts else None
