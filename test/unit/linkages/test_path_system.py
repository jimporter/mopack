import os
import shutil
from os.path import abspath
from textwrap import dedent
from unittest import mock

from . import MockPackage, through_json, LinkageTest
from .. import rehydrate_kwargs
from ... import call_pkg_config, test_stage_dir

from mopack.linkages import Linkage
from mopack.linkages.path_system import PathLinkage, SystemLinkage
from mopack.options import Options
from mopack.metadata import Metadata
from mopack.path import Path
from mopack.shell import ShellArguments
from mopack.types import dependency_string, FieldValueError


def abspathobj(p):
    return Path(p, 'absolute')


def srcpathobj(p):
    return Path(p, 'srcdir')


def buildpathobj(p):
    return Path(p, 'builddir')


def boost_getdir(name, default, options):
    root = options['env'].get('BOOST_ROOT')
    p = options['env'].get('BOOST_{}DIR'.format(name),
                           (os.path.join(root, default) if root else None))
    return [abspath(p)] if p is not None else []


def mock_isfile(p, variables={}):
    p = os.path.normcase(p.string(**variables))
    return p.startswith(os.path.normcase(abspath('/mock')) + os.sep)


class TestPath(LinkageTest):
    linkage_type = PathLinkage
    type = 'path'
    symbols = Options.default().expr_symbols
    pkgdir = os.path.join(test_stage_dir, 'linkage')
    pkgconfdir = os.path.join(pkgdir, 'pkgconfig')
    srcdir = abspath('/mock/srcdir')
    builddir = abspath('/mock/builddir')

    def setUp(self):
        super().setUp()
        self.clear_pkgdir()

    def clear_pkgdir(self):
        if os.path.exists(self.pkgdir):
            shutil.rmtree(self.pkgdir)

    def check_linkage(self, linkage, *, name='foo', auto_link=False,
                      dependencies=[], include_path=[], library_path=[],
                      headers=[], libraries=None, compile_flags=[],
                      link_flags=[]):
        if libraries is None:
            libraries = [name]
        self.assertEqual(linkage.auto_link, auto_link)
        self.assertEqual(linkage.dependencies, dependencies)
        self.assertEqual(linkage.include_path, include_path)
        self.assertEqual(linkage.library_path, library_path)
        self.assertEqual(linkage.headers, headers)
        self.assertEqual(linkage.libraries, libraries)
        self.assertEqual(linkage.compile_flags, ShellArguments(compile_flags))
        self.assertEqual(linkage.link_flags, ShellArguments(link_flags))

    def check_version(self, linkage, expected=None, *, pkg=None, header=None):
        open_args = ({'new': mock.mock_open(read_data=header)} if header
                     else {'side_effect': AssertionError()})
        if pkg is None:
            pkg = MockPackage()

        with mock.patch('subprocess.run', side_effect=OSError()), \
             mock.patch('mopack.linkages.path_system._system_include_path',
                        return_value=[Path('/mock/include')]), \
             mock.patch('mopack.linkages.path_system.isfile', mock_isfile), \
             mock.patch('builtins.open', **open_args):
            self.assertEqual(linkage.version(self.metadata, pkg), expected)

    def check_get_linkage(self, linkage, name, submodules, expected=None, *,
                          pkg=None, metadata=None, write_pkg_config=True):
        depname = dependency_string(name, submodules)
        if expected is None:
            expected = {'name': depname, 'type': self.type, 'generated': True,
                        'auto_link': False, 'pcnames': [depname],
                        'pkg_config_path': [self.pkgconfdir]}

        if pkg is None:
            pkg = MockPackage(name)
        if metadata is None:
            metadata = self.metadata

        self.clear_pkgdir()

        with mock.patch('mopack.linkages.path_system.file_outdated',
                        return_value=write_pkg_config), \
             mock.patch('mopack.linkages.path_system._system_include_path',
                        return_value=[Path('/mock/include')]), \
             mock.patch('mopack.linkages.path_system._system_lib_path',
                        return_value=[Path('/mock/lib')]), \
             mock.patch('mopack.linkages.path_system._system_lib_names',
                        return_value=['lib{}.so']), \
             mock.patch('mopack.linkages.path_system.isfile',
                        mock_isfile):
            self.assertEqual(linkage.get_linkage(metadata, pkg, submodules),
                             expected)

    def check_pkg_config(self, name, submodules, expected={}):
        pcname = dependency_string(name, submodules)
        self.assertCountEqual(
            call_pkg_config(pcname, ['--cflags'], path=self.pkgconfdir),
            expected.get('cflags', [])
        )
        self.assertCountEqual(
            call_pkg_config(pcname, ['--libs'], path=self.pkgconfdir),
            expected.get('libs', ['-L' + abspath('/mock/lib'), '-l' + name])
        )
        self.assertEqual(
            call_pkg_config(pcname, ['--modversion'], path=self.pkgconfdir,
                            split=False),
            expected.get('version', '')
        )

    def test_basic(self):
        linkage = self.make_linkage('foo')
        self.check_linkage(linkage)
        self.check_get_linkage(linkage, 'foo', None)
        self.check_pkg_config('foo', None)

    def test_pkg_config_up_to_date(self):
        linkage = self.make_linkage('foo')
        self.check_linkage(linkage)
        self.check_get_linkage(linkage, 'foo', None, write_pkg_config=False)
        self.assertFalse(os.path.exists(
            os.path.join(self.pkgconfdir, 'foo.pc')
        ))

    def test_auto_link(self):
        pkg = MockPackage(srcdir=self.srcdir, builddir=self.builddir)
        linkage = self.make_linkage('foo', auto_link=True)
        self.check_linkage(linkage, auto_link=True, libraries=[])
        self.check_get_linkage(linkage, 'foo', None, {
            'name': 'foo', 'type': self.type, 'generated': True,
            'auto_link': True, 'pcnames': ['foo'],
            'pkg_config_path': [self.pkgconfdir],
        }, pkg=pkg)
        self.check_pkg_config('foo', None, {
            'libs': ['-L' + abspath('/mock/lib')],
        })

        libdir = abspath('/mock/path/to/lib')
        linkage = self.make_linkage('foo', auto_link=True,
                                    library_path='/mock/path/to/lib')
        self.check_linkage(linkage, auto_link=True, libraries=[],
                           library_path=[abspathobj('/mock/path/to/lib')])
        self.check_get_linkage(linkage, 'foo', None, {
            'name': 'foo', 'type': self.type, 'generated': True,
            'auto_link': True, 'pcnames': ['foo'],
            'pkg_config_path': [self.pkgconfdir],
        }, pkg=pkg)
        self.check_pkg_config('foo', None, {'libs': ['-L' + libdir]})

    def test_version(self):
        linkage = self.make_linkage('foo', version='1.0')
        self.check_linkage(linkage)

        self.check_version(linkage, '1.0')
        self.check_get_linkage(linkage, 'foo', None)
        self.check_pkg_config('foo', None, {'version': '1.0'})

        self.check_version(linkage, '1.0', pkg=MockPackage(version='2.0'))
        self.check_get_linkage(linkage, 'foo', None)
        self.check_pkg_config('foo', None, {'version': '1.0'})

        linkage = self.make_linkage('foo')
        self.check_version(linkage, '2.0', pkg=MockPackage(version='2.0'))
        self.check_get_linkage(linkage, 'foo', None,
                               pkg=MockPackage(version='2.0'))
        self.check_pkg_config('foo', None, {'version': '2.0'})

    def test_version_regex(self):
        good_header = dedent("""\
            // This is a header
            #define VERSION "1.0"
        """)
        uscore_header = dedent("""\
            // This is a header
            #define VERSION "1_0"
        """)
        bad_header = dedent("""\
            // This is a header
        """)

        linkage = self.make_linkage('foo', headers=['foo.hpp'], version={
            'type': 'regex',
            'file': 'foo.hpp',
            'regex': [r'#define VERSION "([\d\.]+)"']
        })
        self.check_linkage(linkage, headers=['foo.hpp'])
        self.check_version(linkage, '1.0', header=good_header)
        self.check_version(linkage, None, header=bad_header)

        linkage = self.make_linkage('foo', headers=['foo.hpp'], version={
            'type': 'regex',
            'file': 'foo.hpp',
            'regex': [r'#define VERSION "([\d_]+)"',
                      ['_', '.']]
        })
        self.check_linkage(linkage, headers=['foo.hpp'])
        self.check_version(linkage, '1.0', header=uscore_header)
        self.check_version(linkage, None, header=bad_header)

    def test_invalid_version(self):
        with self.assertRaises(FieldValueError):
            self.make_linkage('foo', version={'type': 'goofy'})

    def test_dependencies(self):
        linkage = self.make_linkage('foo', dependencies=['bar'])
        self.check_linkage(linkage, dependencies=[('bar', None)])
        self.check_get_linkage(linkage, 'foo', None)
        self.check_pkg_config('foo', None, {
            'libs': ['-L' + abspath('/mock/lib'), '-lfoo', '-lbar'],
        })

        path = '/mock/pkgconfig'
        dep_linkage = {'name': 'foo', 'type': self.type, 'generated': True,
                       'auto_link': True, 'pcnames': ['bar'],
                       'pkg_config_path': [path]}
        with mock.patch('mopack.origins.Package.get_linkage',
                        return_value=dep_linkage):
            self.check_get_linkage(linkage, 'foo', None, {
                'name': 'foo', 'type': self.type, 'generated': True,
                'auto_link': True, 'pcnames': ['foo'],
                'pkg_config_path': [self.pkgconfdir, path],
            })

    def test_include_path_relative(self):
        pkg = MockPackage(srcdir=self.srcdir, builddir=self.builddir)
        incdir = os.path.join(self.srcdir, 'include')
        linkage = self.make_linkage('foo', include_path='include',
                                    headers=['foo.hpp'])
        self.check_linkage(linkage, include_path=[srcpathobj('include')],
                           headers=['foo.hpp'])
        self.check_get_linkage(linkage, 'foo', None, pkg=pkg)
        self.check_pkg_config('foo', None, {'cflags': ['-I' + incdir]})

        linkage = self.make_linkage('foo', include_path=['include'],
                                    headers=['foo.hpp'])
        self.check_linkage(linkage, include_path=[srcpathobj('include')],
                           headers=['foo.hpp'])
        self.check_get_linkage(linkage, 'foo', None, pkg=pkg)
        self.check_pkg_config('foo', None, {'cflags': ['-I' + incdir]})

    def test_include_path_srcdir(self):
        pkg = MockPackage(srcdir=self.srcdir, builddir=self.builddir)
        incdir = os.path.join(self.srcdir, 'include')
        linkage = self.make_linkage('foo', include_path='$srcdir/include',
                                    headers=['foo.hpp'])
        self.check_linkage(linkage, include_path=[srcpathobj('include')],
                           headers=['foo.hpp'])
        self.check_get_linkage(linkage, 'foo', None, pkg=pkg)
        self.check_pkg_config('foo', None, {'cflags': ['-I' + incdir]})

        linkage = self.make_linkage('foo', include_path=['$srcdir/include'],
                                    headers=['foo.hpp'])
        self.check_linkage(linkage, include_path=[srcpathobj('include')],
                           headers=['foo.hpp'])
        self.check_get_linkage(linkage, 'foo', None, pkg=pkg)
        self.check_pkg_config('foo', None, {'cflags': ['-I' + incdir]})

    def test_include_path_builddir(self):
        pkg = MockPackage(srcdir=self.srcdir, builddir=self.builddir)
        incdir = os.path.join(self.builddir, 'include')
        linkage = self.make_linkage('foo', include_path='$builddir/include',
                                    headers=['foo.hpp'])
        self.check_linkage(linkage, include_path=[buildpathobj('include')],
                           headers=['foo.hpp'])
        self.check_get_linkage(linkage, 'foo', None, pkg=pkg)
        self.check_pkg_config('foo', None, {'cflags': ['-I' + incdir]})

        linkage = self.make_linkage('foo', include_path=['$builddir/include'],
                                    headers=['foo.hpp'])
        self.check_linkage(linkage, include_path=[buildpathobj('include')],
                           headers=['foo.hpp'])
        self.check_get_linkage(linkage, 'foo', None, pkg=pkg)
        self.check_pkg_config('foo', None, {'cflags': ['-I' + incdir]})

    def test_include_path_absolute(self):
        pkg = MockPackage(srcdir=self.srcdir, builddir=self.builddir)
        incdir = abspath('/mock/path/to/include')
        incdirobj = abspathobj('/mock/path/to/include')
        linkage = self.make_linkage(
            'foo', include_path='/mock/path/to/include', headers=['foo.hpp']
        )
        self.check_linkage(linkage, include_path=[incdirobj],
                           headers=['foo.hpp'])
        self.check_get_linkage(linkage, 'foo', None, pkg=pkg)
        self.check_pkg_config('foo', None, {'cflags': ['-I' + incdir]})

        linkage = self.make_linkage(
            'foo', include_path='/mock/path/to/include', headers=['foo.hpp']
        )
        self.check_linkage(linkage, include_path=[incdirobj],
                           headers=['foo.hpp'])
        self.check_get_linkage(linkage, 'foo', None)
        self.check_pkg_config('foo', None, {'cflags': ['-I' + incdir]})

    def test_invalid_include_path(self):
        with self.assertRaises(FieldValueError):
            self.make_linkage('foo', include_path='../include')

    def test_library_path_relative(self):
        pkg = MockPackage(srcdir=self.srcdir, builddir=self.builddir)
        libdir = os.path.join(self.builddir, 'lib')
        linkage = self.make_linkage('foo', library_path='lib')
        self.check_linkage(linkage, library_path=[buildpathobj('lib')])
        self.check_get_linkage(linkage, 'foo', None, pkg=pkg)
        self.check_pkg_config('foo', None, {'libs': ['-L' + libdir, '-lfoo']})

        linkage = self.make_linkage('foo', library_path=['lib'])
        self.check_linkage(linkage, library_path=[buildpathobj('lib')])
        self.check_get_linkage(linkage, 'foo', None, pkg=pkg)
        self.check_pkg_config('foo', None, {'libs': ['-L' + libdir, '-lfoo']})

    def test_library_path_srcdir(self):
        pkg = MockPackage(srcdir=self.srcdir, builddir=self.builddir)
        libdir = os.path.join(self.srcdir, 'lib')
        linkage = self.make_linkage('foo', library_path='$srcdir/lib')
        self.check_linkage(linkage, library_path=[srcpathobj('lib')])
        self.check_get_linkage(linkage, 'foo', None, pkg=pkg)
        self.check_pkg_config('foo', None, {'libs': ['-L' + libdir, '-lfoo']})

        linkage = self.make_linkage('foo', library_path=['$srcdir/lib'])
        self.check_linkage(linkage, library_path=[srcpathobj('lib')])
        self.check_get_linkage(linkage, 'foo', None, pkg=pkg)
        self.check_pkg_config('foo', None, {'libs': ['-L' + libdir, '-lfoo']})

    def test_library_path_builddir(self):
        pkg = MockPackage(srcdir=self.srcdir, builddir=self.builddir)
        libdir = os.path.join(self.builddir, 'lib')
        linkage = self.make_linkage('foo', library_path='$builddir/lib')
        self.check_linkage(linkage, library_path=[buildpathobj('lib')])
        self.check_get_linkage(linkage, 'foo', None, pkg=pkg)
        self.check_pkg_config('foo', None, {'libs': ['-L' + libdir, '-lfoo']})

        linkage = self.make_linkage('foo', library_path=['$builddir/lib'])
        self.check_linkage(linkage, library_path=[buildpathobj('lib')])
        self.check_get_linkage(linkage, 'foo', None, pkg=pkg)
        self.check_pkg_config('foo', None, {'libs': ['-L' + libdir, '-lfoo']})

    def test_library_path_absolute(self):
        pkg = MockPackage(srcdir=self.srcdir, builddir=self.builddir)
        libdir = abspath('/mock/path/to/lib')
        linkage = self.make_linkage('foo', library_path='/mock/path/to/lib')
        self.check_linkage(linkage,
                           library_path=[abspathobj('/mock/path/to/lib')])
        self.check_get_linkage(linkage, 'foo', None, pkg=pkg)
        self.check_pkg_config('foo', None, {'libs': ['-L' + libdir, '-lfoo']})

        linkage = self.make_linkage('foo', library_path='/mock/path/to/lib')
        self.check_linkage(linkage,
                           library_path=[abspathobj('/mock/path/to/lib')])
        self.check_get_linkage(linkage, 'foo', None)
        self.check_pkg_config('foo', None, {'libs': ['-L' + libdir, '-lfoo']})

    def test_invalid_library_path(self):
        with self.assertRaises(FieldValueError):
            self.make_linkage('foo', library_path='../lib')

    def test_headers(self):
        linkage = self.make_linkage('foo', headers='foo.hpp')
        self.check_linkage(linkage, headers=['foo.hpp'])
        self.check_get_linkage(linkage, 'foo', None)
        self.check_pkg_config('foo', None, {
            'cflags': ['-I' + abspath('/mock/include')],
        })

        linkage = self.make_linkage('foo', headers=['foo.hpp'])
        self.check_linkage(linkage, headers=['foo.hpp'])
        self.check_get_linkage(linkage, 'foo', None)
        self.check_pkg_config('foo', None, {
            'cflags': ['-I' + abspath('/mock/include')],
        })

    def test_libraries(self):
        linkage = self.make_linkage('foo', libraries='bar')
        self.check_linkage(linkage, libraries=['bar'])
        self.check_get_linkage(linkage, 'foo', None)
        self.check_pkg_config('foo', None, {
            'libs': ['-L' + abspath('/mock/lib'), '-lbar'],
        })

        linkage = self.make_linkage('foo', libraries=['bar'])
        self.check_linkage(linkage, libraries=['bar'])
        self.check_get_linkage(linkage, 'foo', None)
        self.check_pkg_config('foo', None, {
            'libs': ['-L' + abspath('/mock/lib'), '-lbar'],
        })

        linkage = self.make_linkage('foo', libraries=None)
        self.check_linkage(linkage, libraries=[])
        self.check_get_linkage(linkage, 'foo', None)
        self.check_pkg_config('foo', None, {'libs': []})

        linkage = self.make_linkage('foo', libraries=[
            {'type': 'library', 'name': 'bar'},
        ])
        self.check_linkage(linkage, libraries=['bar'])
        self.check_get_linkage(linkage, 'foo', None)
        self.check_pkg_config('foo', None, {
            'libs': ['-L' + abspath('/mock/lib'), '-lbar'],
        })

        linkage = self.make_linkage('foo', libraries=[
            {'type': 'framework', 'name': 'bar'},
        ])
        self.check_linkage(linkage, libraries=[
            {'type': 'framework', 'name': 'bar'},
        ])
        self.check_get_linkage(linkage, 'foo', None)
        self.check_pkg_config('foo', None, {'libs': ['-framework', 'bar']})

    def test_compile_flags(self):
        linkage = self.make_linkage('foo', compile_flags='-pthread -fPIC')
        self.check_linkage(linkage, compile_flags=['-pthread', '-fPIC'])
        self.check_get_linkage(linkage, 'foo', None)
        self.check_pkg_config('foo', None, {'cflags': ['-pthread', '-fPIC']})

        linkage = self.make_linkage('foo', compile_flags=['-pthread', '-fPIC'])
        self.check_linkage(linkage, compile_flags=['-pthread', '-fPIC'])
        self.check_get_linkage(linkage, 'foo', None)
        self.check_pkg_config('foo', None, {'cflags': ['-pthread', '-fPIC']})

    def test_link_flags(self):
        linkage = self.make_linkage('foo', link_flags='-pthread -fPIC')
        self.check_linkage(linkage, link_flags=['-pthread', '-fPIC'])
        self.check_get_linkage(linkage, 'foo', None)
        self.check_pkg_config('foo', None, {
            'libs': ['-pthread', '-fPIC', '-L' + abspath('/mock/lib'),
                     '-lfoo'],
        })

        linkage = self.make_linkage('foo', link_flags=['-pthread', '-fPIC'])
        self.check_linkage(linkage, link_flags=['-pthread', '-fPIC'])
        self.check_get_linkage(linkage, 'foo', None)
        self.check_pkg_config('foo', None, {
            'libs': ['-pthread', '-fPIC', '-L' + abspath('/mock/lib'),
                     '-lfoo'],
        })

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        pkg = MockPackage('foo', submodules=submodules_required,
                          _options=self.make_options())
        linkage = self.make_linkage(pkg)
        self.check_linkage(linkage, libraries=[])
        self.check_get_linkage(linkage, 'foo', ['sub'], pkg=pkg)
        self.check_pkg_config('foo', ['sub'], {
            'libs': ['-L' + abspath('/mock/lib'), '-lfoo_sub'],
        })

        linkage = self.make_linkage(pkg, libraries=['bar'])
        self.check_linkage(linkage, libraries=['bar'])
        self.check_get_linkage(linkage, 'foo', ['sub'], pkg=pkg)
        self.check_pkg_config('foo', ['sub'], {
            'libs': ['-L' + abspath('/mock/lib'), '-lbar', '-lfoo_sub'],
        })

        pkg = MockPackage('foo', submodules=submodules_optional,
                          _options=self.make_options())
        linkage = self.make_linkage(pkg)
        self.check_linkage(linkage, libraries=['foo'])
        self.check_get_linkage(linkage, 'foo', ['sub'], pkg=pkg)
        self.check_pkg_config('foo', ['sub'], {
            'libs': ['-L' + abspath('/mock/lib'), '-lfoo', '-lfoo_sub'],
        })

        linkage = self.make_linkage(pkg, libraries=['bar'])
        self.check_linkage(linkage, libraries=['bar'])
        self.check_get_linkage(linkage, 'foo', ['sub'], pkg=pkg)
        self.check_pkg_config('foo', ['sub'], {
            'libs': ['-L' + abspath('/mock/lib'), '-lbar', '-lfoo_sub'],
        })

    def test_submodule_map(self):
        submodules_required = {'names': '*', 'required': True}

        pkg = MockPackage('foo', submodules=submodules_required,
                          _options=self.make_options())
        linkage = self.make_linkage(pkg, submodule_map='$submodule')
        self.check_linkage(linkage, libraries=[])
        self.check_get_linkage(linkage, 'foo', ['sub'], pkg=pkg)
        self.check_pkg_config('foo', ['sub'], {
            'libs': ['-L' + abspath('/mock/lib'), '-lsub'],
        })

        linkage = self.make_linkage(pkg, submodule_map={
            '*': {'libraries': '$submodule'},
        })
        self.check_linkage(linkage, libraries=[])
        self.check_get_linkage(linkage, 'foo', ['sub'], pkg=pkg)
        self.check_pkg_config('foo', ['sub'], {
            'libs': ['-L' + abspath('/mock/lib'), '-lsub'],
        })

        linkage = self.make_linkage(pkg, submodule_map={'sub': {
            'include_path': '/mock/sub/incdir',
            'library_path': '/mock/sub/libdir',
            'headers': 'sub.hpp',
            'libraries': 'sublib',
            'compile_flags': '-Dsub',
            'link_flags': '-Wl,-sub',
        }, '*': {'libraries': '$submodule'}})
        self.check_linkage(linkage, libraries=[])
        self.check_get_linkage(linkage, 'foo', ['sub'], pkg=pkg)
        self.check_pkg_config('foo', ['sub'], {
            'cflags': ['-Dsub', '-I' + abspath('/mock/sub/incdir')],
            'libs': ['-L' + abspath('/mock/sub/libdir'), '-Wl,-sub',
                     '-lsublib'],
        })
        self.check_get_linkage(linkage, 'foo', ['sub2'], pkg=pkg)
        self.check_pkg_config('foo', ['sub2'], {
            'libs': ['-L' + abspath('/mock/lib'), '-lsub2'],
        })

        pkg = MockPackage(srcdir=self.srcdir, builddir=self.builddir,
                          submodules=submodules_required,
                          _options=self.make_options())
        linkage = self.make_linkage(pkg, submodule_map={
            'sub': {
                'include_path': '$srcdir/$submodule',
                'library_path': '$builddir/$submodule',
                'headers': '$submodule/file.hpp',
                'libraries': '$submodule',
                'compile_flags': '-D$submodule',
                'link_flags': '-Wl,-$submodule',
            },
            '*': {
                'include_path': '$srcdir/star/$submodule',
                'library_path': '$builddir/star/$submodule',
                'headers': 'star/$submodule/file.hpp',
                'libraries': 'star$submodule',
                'compile_flags': '-Dstar$submodule',
                'link_flags': '-Wl,-star$submodule',
            },
        })
        self.check_linkage(linkage, libraries=[])
        self.check_get_linkage(linkage, 'foo', ['sub'], pkg=pkg)
        self.check_pkg_config('foo', ['sub'], {
            'cflags': ['-Dsub', '-I' + abspath('/mock/srcdir/sub')],
            'libs': ['-L' + abspath('/mock/builddir/sub'), '-Wl,-sub',
                     '-lsub'],
        })
        self.check_get_linkage(linkage, 'foo', ['sub2'], pkg=pkg)
        self.check_pkg_config('foo', ['sub2'], {
            'cflags': ['-Dstarsub2', '-I' + abspath('/mock/srcdir/star/sub2')],
            'libs': ['-L' + abspath('/mock/builddir/star/sub2'),
                     '-Wl,-starsub2', '-lstarsub2'],
        })

        linkage = self.make_linkage(pkg, submodule_map={
            'sub': {
                'dependencies': 'foo[sub2]',
                'compile_flags': '-D$submodule',
            },
            '*': {
                'compile_flags': '-Dstar$submodule',
            },
        })
        self.check_linkage(linkage, libraries=[])

        def mock_pkg_get_linkage(self, metadata, submodules):
            return linkage.get_linkage(metadata, pkg, submodules)

        with mock.patch('mopack.origins.Package.get_linkage',
                        mock_pkg_get_linkage):
            self.check_get_linkage(linkage, 'foo', ['sub'], pkg=pkg)
        self.check_pkg_config('foo', ['sub'], {
            'cflags': ['-Dsub', '-Dstarsub2'],
            'libs': [],
        })

    def test_boost(self):
        header = dedent("""\
            #define BOOST_LIB_VERSION "1_23"
        """)
        submodules = {'names': '*', 'required': False}
        for plat in ['linux', 'darwin', 'windows']:
            opts = self.make_options(common_options={'target_platform': plat})
            metadata = Metadata(self.pkgdir, opts)
            pkg = MockPackage('boost', submodules=submodules, _options=opts)
            linkage = self.make_linkage(pkg)
            self.check_linkage(linkage, name='boost')
            self.check_version(linkage, None, header=header)
            self.check_get_linkage(linkage, 'boost', None, {
                'name': 'boost', 'type': self.type, 'generated': True,
                'auto_link': False, 'pcnames': ['boost'],
                'pkg_config_path': [self.pkgconfdir],
            }, pkg=pkg)
            self.check_pkg_config('boost', None)
            self.check_get_linkage(linkage, 'boost', ['thread'], {
                'name': 'boost[thread]', 'type': self.type, 'generated': True,
                'auto_link': False, 'pcnames': ['boost[thread]'],
                'pkg_config_path': [self.pkgconfdir],
            }, pkg=pkg, metadata=metadata)
            self.check_pkg_config('boost', ['thread'], {
                'libs': ['-L' + abspath('/mock/lib'), '-lboost',
                         '-lboost_thread'],
            })

            linkage = self.make_linkage(pkg, inherit_defaults=True)
            self.check_linkage(linkage, name='boost',
                               auto_link=(plat == 'windows'),
                               headers=['boost/version.hpp'], libraries=[])
            self.check_version(linkage, '1.23', header=header)
            self.check_get_linkage(linkage, 'boost', None, {
                'name': 'boost', 'type': self.type, 'generated': True,
                'auto_link': plat == 'windows', 'pcnames': ['boost'],
                'pkg_config_path': [self.pkgconfdir],
            }, pkg=pkg, metadata=metadata)
            self.check_pkg_config('boost', None, {
                'cflags': ['-I' + abspath('/mock/include')],
                'libs': (['-L' + abspath('/mock/lib')]
                         if plat == 'windows' else []),
            })
            self.check_get_linkage(linkage, 'boost', ['thread'], {
                'name': 'boost[thread]', 'type': self.type, 'generated': True,
                'auto_link': plat == 'windows',
                'pcnames': ['boost[thread]' if plat != 'windows' else 'boost'],
                'pkg_config_path': [self.pkgconfdir],
            }, pkg=pkg, metadata=metadata)
            sub = ['thread'] if plat != 'windows' else None
            self.check_pkg_config('boost', sub, {
                'cflags': ( ['-I' + abspath('/mock/include')] +
                            (['-pthread'] if plat != 'windows' else []) ),
                'libs': ( ['-L' + abspath('/mock/lib')] +
                          (['-pthread'] if plat == 'linux' else []) +
                          (['-lboost_thread'] if plat != 'windows' else []) ),
            })

            linkage = self.make_linkage(pkg, inherit_defaults=True,
                                        libraries=['boost'])
            self.check_linkage(
                linkage, name='boost', auto_link=(plat == 'windows'),
                headers=['boost/version.hpp'], libraries=['boost'],
                include_path=[], library_path=[]
            )
            self.check_version(linkage, '1.23', header=header)
            self.check_get_linkage(linkage, 'boost', None, {
                'name': 'boost', 'type': self.type, 'generated': True,
                'auto_link': plat == 'windows', 'pcnames': ['boost'],
                'pkg_config_path': [self.pkgconfdir],
            }, pkg=pkg, metadata=metadata)
            self.check_pkg_config('boost', None, {
                'cflags': ['-I' + abspath('/mock/include')]
            })
            extra_libs = ['boost_regex'] if plat != 'windows' else []
            self.check_get_linkage(linkage, 'boost', ['regex'], {
                'name': 'boost[regex]', 'type': self.type, 'generated': True,
                'auto_link': plat == 'windows',
                'pcnames': ['boost[regex]' if plat != 'windows' else 'boost'],
                'pkg_config_path': [self.pkgconfdir],
            }, pkg=pkg, metadata=metadata)
            sub = ['regex'] if plat != 'windows' else None
            self.check_pkg_config('boost', sub, {
                'cflags': ['-I' + abspath('/mock/include')],
                'libs': (['-L' + abspath('/mock/lib')] +
                         ['-l' + i for i in ['boost'] + extra_libs]),
            })

    def test_boost_env_vars(self):
        header = dedent("""\
            #define BOOST_LIB_VERSION "1_23"
        """)
        submodules = {'names': '*', 'required': False}
        boost_root = abspath('/mock/boost')
        boost_inc = abspath('/mock/boost/inc')
        boost_lib = abspath('/mock/boost/lib')
        common_opts = {'target_platform': 'linux', 'env': {
            'BOOST_ROOT': boost_root,
            'BOOST_INCLUDEDIR': boost_inc,
        }}
        pathobjs = {
            'include_path': [abspathobj(boost_inc)],
            'library_path': [abspathobj(boost_lib)],
        }

        opts = self.make_options(common_options=common_opts)
        metadata = Metadata(self.pkgdir, opts)
        pkg = MockPackage('boost', submodules=submodules, _options=opts)
        linkage = self.make_linkage(pkg, inherit_defaults=True)
        self.check_linkage(linkage, name='boost', auto_link=False,
                           headers=['boost/version.hpp'], libraries=[],
                           **pathobjs)
        self.check_get_linkage(linkage, 'boost', None, pkg=pkg,
                               metadata=metadata)
        self.check_version(linkage, '1.23', header=header)
        self.check_pkg_config('boost', None, {
            'cflags': ['-I{}'.format(boost_inc)], 'libs': [],
        })
        self.check_get_linkage(linkage, 'boost', ['thread'], pkg=pkg,
                               metadata=metadata)
        self.check_pkg_config('boost', ['thread'], {
            'cflags': ['-I{}'.format(boost_inc), '-pthread'],
            'libs': ['-L{}'.format(boost_lib), '-pthread', '-lboost_thread'],
        })

        linkage = self.make_linkage(pkg, inherit_defaults=True,
                                    libraries=['boost'])
        self.check_linkage(linkage, name='boost', auto_link=False,
                           headers=['boost/version.hpp'], libraries=['boost'],
                           **pathobjs)
        self.check_version(linkage, '1.23', header=header)
        self.check_get_linkage(linkage, 'boost', None, pkg=pkg,
                               metadata=metadata)
        self.check_pkg_config('boost', None, {
            'cflags': ['-I{}'.format(boost_inc)],
            'libs': ['-L{}'.format(boost_lib), '-lboost'],
        })
        self.check_get_linkage(linkage, 'boost', ['regex'], pkg=pkg,
                               metadata=metadata)
        self.check_pkg_config('boost', ['regex'], {
            'cflags': ['-I{}'.format(boost_inc)],
            'libs': ['-L{}'.format(boost_lib), '-lboost', '-lboost_regex'],
        })

    def test_pthread(self):
        linkage = self.make_linkage(
            'pthread', inherit_defaults=True,
            common_options={'target_platform': 'linux'}
        )
        self.check_linkage(linkage, name='pthread', libraries=[],
                           compile_flags=['-pthread'],
                           link_flags=['-pthread'])
        self.check_get_linkage(linkage, 'pthread', None)
        self.check_pkg_config('pthread', None, {
            'cflags': ['-pthread'],
            'libs': ['-pthread'],
        })

        linkage = self.make_linkage(
            'pthread', inherit_defaults=True,
            common_options={'target_platform': 'darwin'}
        )
        self.check_linkage(linkage, name='pthread', libraries=[],
                           compile_flags=['-pthread'])
        self.check_get_linkage(linkage, 'pthread', None)
        self.check_pkg_config('pthread', None, {
            'cflags': ['-pthread'],
            'libs': [],
        })

    def test_gl(self):
        linkage = self.make_linkage(
            'gl', inherit_defaults=True,
            common_options={'target_platform': 'linux'}
        )
        self.check_linkage(linkage, name='gl', libraries=['GL'])
        self.check_get_linkage(linkage, 'gl', None)
        self.check_pkg_config('gl', None, {
            'libs': ['-L' + abspath('/mock/lib'), '-lGL'],
        })

        linkage = self.make_linkage(
            'gl', inherit_defaults=True,
            common_options={'target_platform': 'darwin'}
        )
        self.check_linkage(linkage, name='gl', libraries=[
            {'type': 'framework', 'name': 'OpenGL'},
        ])
        self.check_get_linkage(linkage, 'gl', None)
        self.check_pkg_config('gl', None, {'libs': ['-framework', 'OpenGL']})

        linkage = self.make_linkage(
            'gl', inherit_defaults=True,
            common_options={'target_platform': 'windows'}
        )
        self.check_linkage(linkage, name='gl', libraries=['opengl32'])
        self.check_get_linkage(linkage, 'gl', None)
        self.check_pkg_config('gl', None, {
            'libs': ['-L' + abspath('/mock/lib'), '-lopengl32'],
        })

        linkage = self.make_linkage(
            'gl', inherit_defaults=True, libraries=['gl'],
            common_options={'target_platform': 'linux'}
        )
        self.check_linkage(linkage, name='gl', libraries=['gl'])
        self.check_get_linkage(linkage, 'gl', None)
        self.check_pkg_config('gl', None)

    def test_rehydrate(self):
        opts = self.make_options()
        symbols = opts.expr_symbols.augment(path_bases=['builddir'])
        pkg = MockPackage('foo', _options=opts)
        linkage = self.linkage_type(pkg, _symbols=symbols)
        data = linkage.dehydrate()
        self.assertEqual(linkage, Linkage.rehydrate(
            data, name=pkg.name, _options=opts, _symbols=symbols,
            **rehydrate_kwargs
        ))

        linkage = self.linkage_type(pkg, compile_flags=['compile'],
                                    link_flags=['link'], _symbols=symbols)
        data = through_json(linkage.dehydrate())
        self.assertEqual(linkage, Linkage.rehydrate(
            data, name=pkg.name, _options=opts, _symbols=symbols,
            **rehydrate_kwargs
        ))

        pkg = MockPackage('foo', srcdir=self.srcdir, builddir=self.builddir,
                          submodules={'names': '*', 'required': False},
                          _options=opts)
        linkage = self.linkage_type(pkg, submodule_map={
            'foosub': {
                'include_path': 'include',
                'library_path': 'lib',
            },
            'barsub': {
                'compile_flags': 'compile',
                'link_flags': 'link',
            },
        }, _symbols=symbols)
        data = through_json(linkage.dehydrate())
        self.assertEqual(linkage, Linkage.rehydrate(
            data, name=pkg.name, _options=opts, _symbols=symbols,
            **rehydrate_kwargs
        ))

    def test_upgrade(self):
        opts = self.make_options()
        symbols = opts.expr_symbols.augment(path_bases=['builddir'])
        data = {'type': self.type, '_version': 0, 'include_path': [],
                'library_path': [], 'compile_flags': [], 'link_flags': []}
        with mock.patch.object(self.linkage_type, 'upgrade',
                               side_effect=self.linkage_type.upgrade) as m:
            linkage = Linkage.rehydrate(data, name='foo', _options=opts,
                                        _symbols=symbols, **rehydrate_kwargs)
            self.assertIsInstance(linkage, self.linkage_type)
            m.assert_called_once()

    def test_invalid_linkage(self):
        opts = self.make_options()
        pkg = MockPackage('foo', builddir=self.builddir, _options=opts)
        with self.assertRaises(FieldValueError):
            self.make_linkage(pkg, library_path='$srcdir/lib')

        pkg = MockPackage('foo', srcdir=self.srcdir, _options=opts)
        with self.assertRaises(FieldValueError):
            self.make_linkage(pkg, include_path='$builddir/include')

        pkg = MockPackage('foo', _options=opts)
        with self.assertRaises(FieldValueError):
            self.make_linkage(pkg, include_path='include')


class TestSystem(TestPath):
    linkage_type = SystemLinkage
    type = 'system'

    def setUp(self):
        self.mock_run = mock.patch('subprocess.run', side_effect=OSError())
        self.mock_run.start()
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.mock_run.stop()

    def check_linkage(self, linkage, *, name='foo', pcname=None, **kwargs):
        super().check_linkage(linkage, name=name, **kwargs)
        if pcname is None:
            pcname = name
        self.assertEqual(linkage.pcname, pcname)

    def check_get_linkage(self, *args, find_pkg_config=False, **kwargs):
        side_effect = None if find_pkg_config else OSError()
        with mock.patch('subprocess.run', side_effect=side_effect):
            super().check_get_linkage(*args, **kwargs)

    def test_pkg_config(self):
        linkage = self.make_linkage('foo')
        self.check_linkage(linkage)
        self.check_get_linkage(linkage, 'foo', None, {
            'name': 'foo', 'type': 'system', 'pcnames': ['foo'],
            'pkg_config_path': [],
        }, find_pkg_config=True)

    def test_pcname(self):
        linkage = self.make_linkage('foo', pcname='foopc')
        self.check_linkage(linkage, pcname='foopc')
        self.check_get_linkage(linkage, 'foo', None)
        self.check_get_linkage(linkage, 'foo', None, {
            'name': 'foo', 'type': 'system', 'pcnames': ['foopc'],
            'pkg_config_path': [],
        }, find_pkg_config=True)

    def test_system_submodule_map(self):
        submodules_required = {'names': '*', 'required': True}

        pkg = MockPackage('foo', submodules=submodules_required,
                          _options=self.make_options())
        linkage = self.make_linkage(pkg, submodule_map={
            '*': {'pcname': '$submodule'},
        })
        self.check_linkage(linkage, libraries=[])
        self.check_get_linkage(linkage, 'foo', ['sub'], {
            'name': 'foo[sub]', 'type': 'system', 'pcnames': ['sub'],
            'pkg_config_path': [],
        }, find_pkg_config=True, pkg=pkg)
        self.check_get_linkage(linkage, 'foo', ['sub'], pkg=pkg)

        linkage = self.make_linkage(pkg, submodule_map={
            'sub': {'pcname': 'subpc'},
            '*': {'pcname': '$submodule'},
        })
        self.check_linkage(linkage, libraries=[])
        self.check_get_linkage(linkage, 'foo', ['sub'], {
            'name': 'foo[sub]', 'type': 'system', 'pcnames': ['subpc'],
            'pkg_config_path': [],
        }, find_pkg_config=True, pkg=pkg)
        self.check_get_linkage(linkage, 'foo', ['sub'], pkg=pkg)
        self.check_get_linkage(linkage, 'foo', ['sub2'], {
            'name': 'foo[sub2]', 'type': 'system', 'pcnames': ['sub2'],
            'pkg_config_path': [],
        }, find_pkg_config=True, pkg=pkg)
        self.check_get_linkage(linkage, 'foo', ['sub2'], pkg=pkg)
