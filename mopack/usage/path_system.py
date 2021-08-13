import os
import re
import subprocess
from itertools import chain

from . import submodule_placeholder, Usage
from .. import types
from ..commands import Metadata
from ..environment import get_pkg_config
from ..freezedried import DictFreezeDryer, FreezeDried, ListFreezeDryer
from ..iterutils import listify
from ..package_defaults import DefaultResolver
from ..path import exists, file_outdated, Path
from ..pkg_config import generated_pkg_config_dir, write_pkg_config
from ..placeholder import placeholder, PlaceholderFD
from ..platforms import package_library_name
from ..shell import ShellArguments, split_paths
from ..types import Unset


# XXX: Getting build configuration like this from the environment is a bit
# hacky. Maybe there's a better way?

def _system_include_path(env=os.environ):
    return [Path(i) for i in split_paths(env.get('MOPACK_INCLUDE_PATH'))]


def _system_lib_path(env=os.environ):
    return [Path(i) for i in split_paths(env.get('MOPACK_LIB_PATH'))]


def _system_lib_names(env=os.environ):
    return split_paths(env.get('MOPACK_LIB_NAMES'))


def _library(field, value):
    try:
        return types.string(field, value)
    except types.FieldError:
        value = types.dict_shape({
            'type': types.constant('library', 'guess', 'framework'),
            'name': types.string
        }, desc='library')(field, value)
        if value['type'] == 'library':
            return value['name']
        return value


def _list_of_paths(base):
    return types.list_of(types.abs_or_inner_path(base), listify=True)


_version_def = types.one_of(
    types.maybe(types.string),
    types.dict_shape({
        'type': types.constant('regex'),
        'file': types.string,
        'regex': types.list_of(
            types.one_of(
                types.string,
                types.list_of_length(types.string, 2),
                desc='string or pair of strings'
            )
        ),
    }, desc='version finder'),
    desc='version definition'
)

_list_of_headers = types.list_of(types.string, listify=True)
_list_of_libraries = types.list_of(_library, listify=True)

_SubmoduleFD = PlaceholderFD(submodule_placeholder)
_PathListFD = ListFreezeDryer(Path)


@FreezeDried.fields(rehydrate={
    'include_path': _SubmoduleFD, 'library_path': _SubmoduleFD,
    'headers': _SubmoduleFD, 'libraries': _SubmoduleFD,
    'compile_flags': _SubmoduleFD, 'link_flags': _SubmoduleFD,
})
class _SubmoduleMapping(FreezeDried):
    def __init__(self, srcbase, buildbase, *, include_path=None,
                 library_path=None, headers=None, libraries=None,
                 compile_flags=None, link_flags=None):
        def P(other):
            return types.placeholder_check(other, submodule_placeholder)

        T = types.TypeCheck(locals())
        T.include_path(P(_list_of_paths(srcbase)))
        T.library_path(P(_list_of_paths(buildbase)))
        T.headers(P(_list_of_headers))
        T.libraries(P(_list_of_libraries))
        T.compile_flags(P(types.shell_args(none_ok=True)))
        T.link_flags(P(types.shell_args(none_ok=True)))

    def fill(self, submodule_name, srcbase, buildbase):
        def P(other):
            return types.placeholder_fill(other, submodule_placeholder,
                                          submodule_name)

        result = type(self).__new__(type(self))
        T = types.TypeCheck(self.__dict__, dest=result)
        T.include_path(P(_list_of_paths(srcbase)))
        T.library_path(P(_list_of_paths(buildbase)))
        T.headers(P(_list_of_headers))
        T.libraries(P(_list_of_libraries))
        T.compile_flags(P(types.shell_args(none_ok=True)))
        T.link_flags(P(types.shell_args(none_ok=True)))
        return result


def _submodule_map(srcbase, buildbase):
    def check_item(field, value):
        with types.wrap_field_error(field):
            return _SubmoduleMapping(srcbase, buildbase, **value)

    def check(field, value):
        try:
            value = {'*': {
                'libraries': types.placeholder_string(field, value)
            }}
        except types.FieldError:
            pass

        return types.dict_of(types.string, check_item)(field, value)

    return check


@FreezeDried.fields(rehydrate={
    'include_path': _PathListFD, 'library_path': _PathListFD,
    'compile_flags': ShellArguments, 'link_flags': ShellArguments,
    'submodule_map': DictFreezeDryer(value_type=_SubmoduleMapping),
})
class PathUsage(Usage):
    type = 'path'
    _version = 1

    @staticmethod
    def upgrade(config, version):
        return config

    def __init__(self, name, *, auto_link=Unset, version=Unset,
                 include_path=Unset, library_path=Unset, headers=Unset,
                 libraries=Unset, compile_flags=Unset, link_flags=Unset,
                 submodule_map=Unset, submodules, _options, _path_bases):
        super().__init__(_options=_options)
        symbols = self._expr_symbols(_path_bases)
        package_default = DefaultResolver(self, symbols, name)
        srcbase = self._preferred_base('srcdir', _path_bases)
        buildbase = self._preferred_base('builddir', _path_bases)

        T = types.TypeCheck(locals(), symbols)
        # XXX: Maybe have the compiler tell *us* if it supports auto-linking,
        # instead of us telling it?
        T.auto_link(package_default(types.boolean, default=False))

        T.version(package_default(_version_def), dest_field='explicit_version')

        # XXX: These specify the *possible* paths to find headers/libraries.
        # Should there be a way of specifying paths that are *always* passed to
        # the compiler?
        T.include_path(package_default(_list_of_paths(srcbase)))
        T.library_path(package_default(_list_of_paths(buildbase)))

        T.headers(package_default(_list_of_headers))

        if self.auto_link or submodules and submodules['required']:
            # If auto-linking or if submodules are required, default to an
            # empty list of libraries, since we likely don't have a "base"
            # library that always needs linking to.
            libs_checker = types.maybe(_list_of_libraries, default=[])
        else:
            libs_checker = package_default(
                _list_of_libraries, default={'type': 'guess', 'name': name}
            )
        T.libraries(libs_checker)
        T.compile_flags(types.shell_args(none_ok=True))
        T.link_flags(types.shell_args(none_ok=True))

        if submodules:
            submodule_var = placeholder(submodule_placeholder)
            extra_symbols = {'submodule': submodule_var}
            T.submodule_map(package_default(
                types.maybe(_submodule_map(srcbase, buildbase)),
                default=name + '_' + submodule_var,
                extra_symbols=extra_symbols
            ), extra_symbols=extra_symbols)

    def _get_submodule_mapping(self, submodule, srcbase, buildbase):
        try:
            mapping = self.submodule_map[submodule]
        except KeyError:
            mapping = self.submodule_map['*']
        return mapping.fill(submodule, srcbase, buildbase)

    def _get_library(self, lib):
        if isinstance(lib, dict) and lib['type'] == 'guess':
            return package_library_name(
                self._common_options.target_platform, lib['name']
            )
        return lib

    @staticmethod
    def _link_library(lib):
        if isinstance(lib, str):
            return ['-l' + lib]

        assert lib['type'] == 'framework'
        return ['-framework', lib['name']]

    @staticmethod
    def _filter_path(fn, path, files, kind):
        filtered = {}
        for f in files:
            for p in path:
                if fn(p, f):
                    filtered[p] = True
                    break
            else:
                raise ValueError('unable to find {} {!r}'.format(kind, f))
        return list(filtered.keys())

    @classmethod
    def _include_dirs(cls, headers, include_path, path_vars):
        headers = listify(headers, scalar_ok=False)
        include_path = (listify(include_path, scalar_ok=False) or
                        _system_include_path())
        return cls._filter_path(
            lambda p, f: exists(p.append(f), path_vars),
            include_path, headers, 'header'
        )

    @classmethod
    def _library_dirs(cls, auto_link, libraries, library_path, path_vars):
        library_path = (listify(library_path, scalar_ok=False)
                        or _system_lib_path())
        if auto_link:
            # When auto-linking, we can't determine the library dirs that are
            # actually used, so include them all.
            return library_path

        lib_names = _system_lib_names()
        return cls._filter_path(
            lambda p, f: any(exists(p.append(i.format(f)), path_vars)
                             for i in lib_names),
            library_path, (i for i in libraries if isinstance(i, str)),
            'library'
        )

    @staticmethod
    def _match_line(ex, line):
        if isinstance(ex, str):
            m = re.search(ex, line)
            line = m.group(1) if m else None
            return line is not None, line
        else:
            return True, re.sub(ex[0], ex[1], line)

    def _get_version(self, pkg, pkgdir, include_dirs, path_vars):
        if isinstance(self.explicit_version, dict):
            version = self.explicit_version
            for path in include_dirs:
                header = path.append(version['file'])
                try:
                    with open(header.string(**path_vars)) as f:
                        for line in f:
                            for ex in version['regex']:
                                found, line = self._match_line(ex, line)
                                if not found:
                                    break
                            else:
                                return line
                except FileNotFoundError:
                    pass
            return None
        elif self.explicit_version is not None:
            return self.explicit_version
        else:
            return pkg.guessed_version(pkgdir)

    def version(self, pkg, pkgdir, srcdir, builddir):
        path_vars = {'srcdir': srcdir, 'builddir': builddir}
        try:
            include_dirs = self._include_dirs(
                self.headers, self.include_path, path_vars
            )
        except ValueError:  # pragma: no cover
            # XXX: This is a hack to work around the fact that we currently
            # require the build system to pass include dirs during `usage` (and
            # really, during `list-packages` too). We should handle this in a
            # smarter way and then remove this.
            include_dirs = []

        return self._get_version(pkg, pkgdir, include_dirs, path_vars)

    def get_usage(self, pkg, submodules, pkgdir, srcdir, builddir):
        path_vars = {'srcdir': srcdir, 'builddir': builddir}

        if submodules and self.submodule_map:
            path_bases = tuple(k for k, v in path_vars.items()
                               if v is not None)
            srcbase = self._preferred_base('srcdir', path_bases)
            buildbase = self._preferred_base('builddir', path_bases)
            mappings = [self._get_submodule_mapping(i, srcbase, buildbase)
                        for i in submodules]
        else:
            mappings = []

        def chain_attr(key):
            yield from getattr(self, key)
            for i in mappings:
                yield from getattr(i, key)

        pkgconfdir = generated_pkg_config_dir(pkgdir)
        pcname = ('{}[{}]'.format(pkg.name, ','.join(submodules))
                  if submodules else pkg.name)
        pcpath = os.path.join(pkgconfdir, pcname + '.pc')

        include_dirs = self._include_dirs(
            chain_attr('headers'), chain_attr('include_path'), path_vars
        )
        libraries = [self._get_library(i) for i in chain_attr('libraries')]
        library_dirs = self._library_dirs(
            self.auto_link, libraries, chain_attr('library_path'), path_vars
        )

        cflags = (
            [('-I', i) for i in include_dirs] +
            ShellArguments(chain_attr('compile_flags'))
        )
        libs = (
            [('-L', i) for i in library_dirs] +
            ShellArguments(chain_attr('link_flags')) +
            chain.from_iterable(self._link_library(i) for i in libraries)
        )
        version = self._get_version(pkg, pkgdir, include_dirs, path_vars) or ''

        metadata_path = os.path.join(pkgdir, Metadata.metadata_filename)
        if file_outdated(pcpath, metadata_path):
            os.makedirs(pkgconfdir, exist_ok=True)
            with open(pcpath, 'w') as f:
                # XXX: It would be nice to write one pkg-config .pc file per
                # submodule instead of writing a single file for all the
                # requested submodules.
                write_pkg_config(f, pcname, version=version, cflags=cflags,
                                 libs=libs, variables=path_vars)

        return self._usage(
            pkg, path=[pkgconfdir], pcfiles=[pcname], generated=True,
            auto_link=self.auto_link
        )


class SystemUsage(PathUsage):
    type = 'system'

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self.pcfile = name

    def version(self, pkg, pkgdir, srcdir, builddir):
        pkg_config = get_pkg_config(self._common_options.env)
        try:
            return subprocess.run(
                pkg_config + [self.pcfile, '--modversion'], check=True,
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                universal_newlines=True
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return super().version(pkg, pkgdir, srcdir, builddir)

    def get_usage(self, pkg, submodules, pkgdir, srcdir, builddir):
        pkg_config = get_pkg_config(self._common_options.env)
        try:
            subprocess.run(pkg_config + [self.pcfile], check=True,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            return self._usage(pkg, path=[], pcfiles=[self.pcfile],
                               extra_args=[])
        except (OSError, subprocess.CalledProcessError):
            return super().get_usage(pkg, submodules, pkgdir, srcdir, builddir)
