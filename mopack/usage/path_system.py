import subprocess
from itertools import chain

from . import Usage
from .. import types
from ..freezedried import FreezeDried, ListFreezeDryer
from ..iterutils import merge_dicts
from ..package_defaults import DefaultResolver
from ..path import Path
from ..platforms import package_library_name
from ..shell import get_cmd
from ..types import Unset


def _library(field, value):
    value = types.dict_shape({
        'type': types.constant('library', 'guess', 'framework'),
        'name': types.string
    }, desc='library')(field, value)
    if value['type'] == 'library':
        return value['name']
    return value


def _list_of_paths(*bases):
    return types.list_of(types.abs_or_inner_path(*bases), listify=True)


_list_of_headers = types.list_of(types.string, listify=True)
_list_of_libraries = types.list_of(types.one_of(
    types.string, _library, desc='library'
), listify=True)


def _submodule_map(srcbases, buildbases):
    def check(field, value):
        try:
            value = {'*': {'libraries': types.string(field, value)}}
        except types.FieldError:
            pass

        return types.dict_of(
            types.string,
            types.dict_shape({
                'include_path': _list_of_paths(*srcbases),
                'library_path': _list_of_paths(*buildbases),
                'headers': _list_of_headers,
                'libraries': _list_of_libraries,
                'compile_flags': types.shell_args(),
                'link_flags': types.shell_args(),
            }, 'a submodule map')
        )(field, value)

    return check


@FreezeDried.fields(rehydrate={'include_path': ListFreezeDryer(Path),
                               'library_path': ListFreezeDryer(Path)})
class PathUsage(Usage):
    type = 'path'

    def __init__(self, name, *, auto_link=Unset, include_path=Unset,
                 library_path=Unset, headers=Unset, libraries=Unset,
                 compile_flags=Unset, link_flags=Unset, submodule_map=Unset,
                 submodules, _options, _path_bases):
        super().__init__(_options=_options)
        package_default = DefaultResolver(self, _options.expr_symbols, name)

        # XXX: This can probably be removed if/when we pull more package
        # resolution logic into mopack.
        self.auto_link = package_default(types.boolean, default=False)(
            'auto_link', auto_link
        )

        srcbases = Path.Base.filter(['srcdir', 'builddir'], _path_bases)
        buildbases = Path.Base.filter(['builddir', 'srcdir'], _path_bases)

        self.include_path = package_default(
            _list_of_paths(*srcbases)
        )('include_path', include_path)
        self.library_path = package_default(
            _list_of_paths(*buildbases)
        )('library_path', library_path)

        self.headers = package_default(_list_of_headers)('headers', headers)

        if submodules and submodules['required']:
            # If submodules are required, default to an empty list of
            # libraries, since we likely don't have a "base" library that
            # always needs linking to.
            libs_checker = types.default(_list_of_libraries, [])
        else:
            libs_checker = package_default(
                _list_of_libraries, default={'type': 'guess', 'name': name}
            )
        self.libraries = libs_checker('libraries', libraries)

        defaulted_flags = types.default(types.shell_args(), [])
        self.compile_flags = defaulted_flags('compile_flags', compile_flags)
        self.link_flags = defaulted_flags('link_flags', link_flags)

        if submodules:
            self.submodule_map = package_default(
                types.maybe(_submodule_map(srcbases, buildbases)),
                default=name + '_{submodule}'
            )('submodule_map', submodule_map)

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
                    self._common_options.target_platform, lib['name']
                )
            return lib

        return [make_library(i) for i in libraries]

    def _get_usage(self, submodules, srcdir, builddir, **kwargs):
        def chain_mapping(key):
            return chain(getattr(self, key), mappings.get(key, []))

        mappings = merge_dicts(*(self._get_submodule_mapping(i)
                                 for i in submodules or []))

        return self._usage(
            auto_link=self.auto_link,
            include_path=[i.string(srcdir=srcdir, builddir=builddir) for i in
                          chain_mapping('include_path')],
            library_path=[i.string(srcdir=srcdir, builddir=builddir) for i in
                          chain_mapping('library_path')],
            headers=list(chain_mapping('headers')),
            libraries=self._get_libraries(chain_mapping('libraries')),
            compile_flags=list(chain_mapping('compile_flags')),
            link_flags=list(chain_mapping('link_flags')),
            **kwargs
        )

    def get_usage(self, submodules, srcdir, builddir):
        return self._get_usage(submodules, srcdir, builddir)


class SystemUsage(PathUsage):
    type = 'system'

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self.pcfile = name

    def get_usage(self, submodules, srcdir, builddir):
        pkg_config = get_cmd(self._common_options.env, 'PKG_CONFIG',
                             'pkg-config')
        try:
            subprocess.run(pkg_config + [self.pcfile], check=True,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            return self._usage(type='pkg-config', path=None,
                               pcfiles=[self.pcfile], extra_args=[])
        except (OSError, subprocess.CalledProcessError):
            return self._get_usage(submodules, srcdir, builddir, type='path')
