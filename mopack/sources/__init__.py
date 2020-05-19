import os
from pkg_resources import load_entry_point

from ..freezedried import FreezeDried
from ..options import BaseOptions
from ..types import try_load_config
from ..usage import Usage, make_usage


def _get_source_type(source):
    try:
        return load_entry_point('mopack', 'mopack.sources', source)
    except ImportError:
        raise ValueError('unknown source {!r}'.format(source))


class Package(FreezeDried):
    _type_field = 'source'
    _get_type = _get_source_type
    _skip_fields = ('global_options',)
    _skip_compare_fields = ('config_file',)

    Options = None

    def __init__(self, name, *, config_file):
        self.name = name
        self.config_file = config_file

    @property
    def config_dir(self):
        return os.path.dirname(self.config_file)

    @property
    def builder_types(self):
        return []

    def set_options(self, options):
        self.global_options = options['sources'].get(self.source)

    def clean_pre(self, pkgdir, new_package):
        return False

    def clean_post(self, pkgdir, new_package):
        return False

    def clean_all(self, pkgdir, new_package):
        return (self.clean_pre(pkgdir, new_package),
                self.clean_post(pkgdir, new_package))

    def fetch(self, pkgdir, parent_config):
        pass

    def _resolved_metadata(self, usage):
        return ResolvedPackage(self, usage)

    @staticmethod
    def _resolved_metadata_all(packages, usage):
        return [p._resolved_metadata(u) for p, u in zip(packages, usage)]

    def __repr__(self):
        return '<{}({!r})>'.format(type(self).__name__, self.name)


class BinaryPackage(Package):
    _rehydrate_fields = {'usage': Usage}

    def __init__(self, name, *, usage, **kwargs):
        super().__init__(name, **kwargs)
        self.usage = (usage if isinstance(usage, Usage) else
                      make_usage(name, usage))

    def set_options(self, options):
        super().set_options(options)
        self.usage.set_options(options)


class PackageOptions(FreezeDried, BaseOptions):
    _type_field = 'source'

    @property
    def _context(self):
        return 'while adding options for {!r} source'.format(self.source)

    @staticmethod
    def _get_type(source):
        return _get_source_type(source).Options


class ResolvedPackage(FreezeDried):
    _rehydrate_fields = {'config': Package}

    def __init__(self, config, usage):
        self.config = config
        self.usage = usage

    def __repr__(self):
        return '<{}({!r}, {!r})>'.format(type(self).__name__, self.config.name,
                                         self.usage)


def make_package(name, config):
    config = config.copy()
    source = config.pop('source')

    context = 'while constructing package {!r}'.format(name)
    with try_load_config(config, context):
        return _get_source_type(source)(name, **config)


def make_package_options(source):
    opts = _get_source_type(source).Options
    return opts() if opts else None
