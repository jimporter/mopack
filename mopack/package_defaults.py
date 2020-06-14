import os
from collections import namedtuple
from types import FunctionType

from . import types

_DeferredDefault = namedtuple('_DeferredDefault', ['function', 'check'])


def _boost_getdir(name, default):
    def wrapper(options):
        root = options.common.env.get('BOOST_ROOT')
        p = options.common.env.get(
            name, os.path.join(root, default) if root else None
        )
        return [os.path.abspath(p)] if p is not None else []

    return wrapper


def _boost_submodule_map(options):
    if options.common.target_platform == 'windows':
        return 'boost_{submodule}'

    link_flags = ('' if options.common.target_platform == 'darwin'
                  else '-pthread')
    return {
        'thread': {
            'libraries': 'boost_thread',
            'compile_flags': '-pthread',
            'link_flags': link_flags,
        },
        '*': {
            'libraries': 'boost_{submodule}',
        },
    }


_defaults = {
    'boost': {
        'source': {
            '*': {
                'submodules': {
                    'names': '*',
                    'required': False,
                },
            },
        },
        'usage': {
            'path/system': {
                'include_path': _boost_getdir('BOOST_INCLUDEDIR', 'include'),
                'library_path': _boost_getdir('BOOST_LIBRARYDIR', 'lib'),
                'headers': ['boost/version.hpp'],
                'libraries': None,
                'submodule_map': _boost_submodule_map,
            },
            'pkg-config': {
                'submodule_map': None,
            },
        },
    },
}


def get_default(package_name, genus, species, field, default=None):
    defaults = _defaults.get(package_name, {}).get(genus, {})
    if species in defaults and field in defaults[species]:
        return defaults[species][field]
    return defaults.get('*', {}).get(field, default)


def package_default(other, package_name, genus, species, field=None,
                    default=None):
    forced_field = field

    def check(field, value):
        if value is types.Unset:
            value = get_default(package_name, genus, species,
                                forced_field or field, default)
            if isinstance(value, FunctionType):
                return _DeferredDefault(value, other)
        return other(field, value)

    return check


def finalize_defaults(options, obj, attrs=None):
    if attrs is None:
        attrs = obj.__dict__
    for k, v in attrs.items():
        if isinstance(v, _DeferredDefault):
            setattr(obj, k, v.check(k, v.function(options)))
