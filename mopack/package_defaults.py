import os

from . import types
from .iterutils import listify


def _boost_getdir(name, root, default):
    p = os.getenv(name, os.path.join(root, default) if root else None)
    return os.path.abspath(p) if p is not None else p


_boost_root = os.getenv('BOOST_ROOT')
_boost_incdir = _boost_getdir('BOOST_INCLUDEDIR', _boost_root, 'include')
_boost_libdir = _boost_getdir('BOOST_LIBRARYDIR', _boost_root, 'lib')

_defaults = {
    'boost': {
        'submodules': {
            'names': '*',
            'required': False,
        },
        'include_path': listify(_boost_incdir),
        'library_path': listify(_boost_libdir),
        'headers': ['boost/version.hpp'],
        'libraries': None,
        'pkg_config_submodule_map': None,
    },
}


def get_default(package_name, field, default=None):
    return _defaults.get(package_name, {}).get(field, default)


def package_default(other, package_name, field=None, default=None):
    forced_field = field

    def check(field, value):
        if value is types.Unset:
            value = get_default(package_name, forced_field or field, default)
        return other(field, value)

    return check
