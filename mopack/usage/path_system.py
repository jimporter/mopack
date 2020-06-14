from itertools import chain

from . import Usage
from .. import path, types
from ..iterutils import merge_dicts
from ..package_defaults import package_default
from ..platforms import package_library_name
from ..types import Unset


def _library(field, value):
    value = types.dict_shape({
        'type': types.constant('library', 'guess', 'framework'),
        'name': types.string
    }, desc='library')(field, value)
    if value['type'] == 'library':
        return value['name']
    return value


_list_of_paths = types.list_of(types.abs_or_inner_path, listify=True)
_list_of_headers = types.list_of(types.string, listify=True)
_list_of_libraries = types.list_of(types.one_of(
    types.string, _library, desc='library'
), listify=True)


def _submodule_map(field, value):
    try:
        value = {'*': {'libraries': types.string(field, value)}}
    except types.FieldError:
        pass

    return types.dict_of(
        types.string,
        types.dict_shape({
            'include_path': _list_of_paths,
            'library_path': _list_of_paths,
            'headers': _list_of_headers,
            'libraries': _list_of_libraries,
            'compile_flags': types.shell_args(),
            'link_flags': types.shell_args(),
        }, 'a submodule map')
    )(field, value)


class PathUsage(Usage):
    type = 'path'

    def __init__(self, name, *, include_path=Unset, library_path=Unset,
                 headers=Unset, libraries=Unset, compile_flags=Unset,
                 link_flags=Unset, submodule_map=Unset, submodules):
        defaulted_paths = self._package_default(_list_of_paths, name)
        self.include_path = defaulted_paths('include_path', include_path)
        self.library_path = defaulted_paths('library_path', library_path)

        self.headers = self._package_default(_list_of_headers, name)(
            'headers', headers
        )

        if submodules and submodules['required']:
            # If submodules are required, default to an empty list of
            # libraries, since we likely don't have a "base" library that
            # always needs linking to.
            libs_checker = types.default(_list_of_libraries, [])
        else:
            libs_checker = self._package_default(
                _list_of_libraries, name,
                default={'type': 'guess', 'name': name}
            )
        self.libraries = libs_checker('libraries', libraries)

        defaulted_flags = types.default(types.shell_args(), [])
        self.compile_flags = defaulted_flags('compile_flags', compile_flags)
        self.link_flags = defaulted_flags('link_flags', link_flags)

        if submodules:
            self.submodule_map = self._package_default(
                types.maybe(_submodule_map), name,
                default=name + '_{submodule}'
            )('submodule_map', submodule_map)

    def _package_default(self, other, name, field=None, default=None):
        return package_default(other, name, 'usage', 'path/system', field,
                               default)

    def _get_submodule_mapping(self, submodule):
        if self.submodule_map is None:
            return {}
        try:
            return self.submodule_map[submodule]
        except KeyError:
            return {k: [i.format(submodule=submodule) for i in v]
                    for k, v in self.submodule_map['*'].items()}

    def _get_libraries(self, libraries):
        def make_library(lib):
            if isinstance(lib, dict) and lib.get('type') == 'guess':
                return package_library_name(
                    self._options.common.target_platform, lib['name']
                )
            return lib

        return [make_library(i) for i in libraries]

    def get_usage(self, submodules, srcdir, builddir):
        def chain_mapping(key):
            return chain(getattr(self, key), mappings.get(key, []))

        mappings = merge_dicts(*(self._get_submodule_mapping(i)
                                 for i in submodules or []))

        try:
            # XXX: Provide a way of specifying what these paths are relative to
            # instead of just assuming that includes are in the srcdir and libs
            # are in the builddir.
            return self._usage(
                include_path=[path.try_join(srcdir, i) for i in
                              chain_mapping('include_path')],
                library_path=[path.try_join(builddir, i) for i in
                              chain_mapping('library_path')],
                headers=list(chain_mapping('headers')),
                libraries=self._get_libraries(chain_mapping('libraries')),
                compile_flags=list(chain_mapping('compile_flags')),
                link_flags=list(chain_mapping('link_flags')),
            )
        except TypeError:
            raise ValueError('unable to use `path` usage with this package ' +
                             'type; try `system` usage')


class SystemUsage(PathUsage):
    type = 'system'
