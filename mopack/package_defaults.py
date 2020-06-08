import os
from types import FunctionType

from . import types


def _boost_getdir(name, default):
    def wrapper(options):
        root = options.common.env.get('BOOST_ROOT')
        p = options.common.env.get(
            name, os.path.join(root, default) if root else None
        )
        return [os.path.abspath(p)] if p is not None else []

    return wrapper


_defaults = {
    'boost': {
        'submodules': {
            'names': '*',
            'required': False,
        },
        'include_path': _boost_getdir('BOOST_INCLUDEDIR', 'include'),
        'library_path': _boost_getdir('BOOST_LIBRARYDIR', 'lib'),
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
            if isinstance(value, FunctionType):
                return value
        return other(field, value)

    return check


def finalize_defaults(options, obj, attrs=None):
    if attrs is None:
        attrs = obj.__dict__
    for k, v in attrs.items():
        if isinstance(v, FunctionType):
            setattr(obj, k, v(options))
