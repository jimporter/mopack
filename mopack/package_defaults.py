from . import types

_defaults = {
    'boost': {
        'submodules': {
            'names': '*',
            'required': False,
        },
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
