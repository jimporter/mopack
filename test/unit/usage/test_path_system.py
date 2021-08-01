import os
import shutil
from os.path import abspath
from unittest import mock

from . import MockPackage, through_json, UsageTest
from ... import call_pkg_config, test_stage_dir

from mopack.iterutils import iterate
from mopack.options import Options
from mopack.path import Path
from mopack.shell import ShellArguments
from mopack.types import FieldError
from mopack.usage import Usage
from mopack.usage.path_system import PathUsage, SystemUsage


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


class TestPath(UsageTest):
    usage_type = PathUsage
    type = 'path'
    symbols = Options.default().expr_symbols
    pkgdir = os.path.join(test_stage_dir, 'usage')
    pkgconfdir = os.path.join(pkgdir, 'pkgconfig')

    def setUp(self):
        self.clear_pkgdir()

    def clear_pkgdir(self):
        if os.path.exists(self.pkgdir):
            shutil.rmtree(self.pkgdir)

    def check_usage(self, usage, *, auto_link=False, include_path=[],
                    library_path=[], headers=[],
                    libraries=[{'type': 'guess', 'name': 'foo'}],
                    compile_flags=[], link_flags=[]):
        self.assertEqual(usage.auto_link, auto_link)
        self.assertEqual(usage.include_path, include_path)
        self.assertEqual(usage.library_path, library_path)
        self.assertEqual(usage.headers, headers)
        self.assertEqual(usage.libraries, libraries)
        self.assertEqual(usage.compile_flags, ShellArguments(compile_flags))
        self.assertEqual(usage.link_flags, ShellArguments(link_flags))

    def check_get_usage(self, usage, name, submodules, srcdir, builddir,
                        expected=None, *, write_pkg_config=True):
        pcname = ('{}[{}]'.format(name, ','.join(iterate(submodules)))
                  if submodules else name)
        if expected is None:
            expected = {
                'name': name, 'type': self.type, 'path': self.pkgconfdir,
                'pcfiles': [pcname], 'requirements': {
                    'auto_link': False, 'headers': [], 'libraries': [name],
                },
            }

        self.clear_pkgdir()
        with mock.patch('mopack.usage.path_system.file_outdated',
                        return_value=write_pkg_config):
            self.assertEqual(usage.get_usage(
                MockPackage(name), submodules, self.pkgdir, srcdir, builddir
            ), expected)

    def check_pkg_config(self, name, submodules, expected={}):
        pcname = ('{}[{}]'.format(name, ','.join(iterate(submodules)))
                  if submodules else name)
        self.assertCountEqual(
            call_pkg_config(pcname, ['--cflags'], path=self.pkgconfdir),
            expected.get('cflags', [])
        )
        self.assertCountEqual(
            call_pkg_config(pcname, ['--libs'], path=self.pkgconfdir),
            expected.get('libs', ['-l' + name])
        )

    def test_basic(self):
        usage = self.make_usage('foo')
        self.check_usage(usage)
        self.check_get_usage(usage, 'foo', None, None, None)
        self.check_pkg_config('foo', None)

    def test_pkg_config_up_to_date(self):
        usage = self.make_usage('foo')
        self.check_usage(usage)
        self.check_get_usage(usage, 'foo', None, None, None,
                             write_pkg_config=False)
        self.assertFalse(os.path.exists(
            os.path.join(self.pkgconfdir, 'foo.pc')
        ))

    def test_auto_link(self):
        usage = self.make_usage('foo', auto_link=True)
        self.check_usage(usage, auto_link=True)
        self.check_get_usage(usage, 'foo', None, self.srcdir, self.builddir, {
            'name': 'foo', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['foo'], 'requirements': {
                'auto_link': True, 'headers': [], 'libraries': ['foo'],
            },
        })
        self.check_pkg_config('foo', None)

    def test_include_path_relative(self):
        incdir = os.path.join(self.srcdir, 'include')
        usage = self.make_usage('foo', include_path='include')
        self.check_usage(usage, include_path=[srcpathobj('include')])
        self.check_get_usage(usage, 'foo', None, self.srcdir, self.builddir)
        self.check_pkg_config('foo', None, {'cflags': ['-I' + incdir]})

        usage = self.make_usage('foo', include_path=['include'])
        self.check_usage(usage, include_path=[srcpathobj('include')])
        self.check_get_usage(usage, 'foo', None, self.srcdir, self.builddir)
        self.check_pkg_config('foo', None, {'cflags': ['-I' + incdir]})

    def test_include_path_srcdir(self):
        incdir = os.path.join(self.srcdir, 'include')
        usage = self.make_usage('foo', include_path='$srcdir/include')
        self.check_usage(usage, include_path=[srcpathobj('include')])
        self.check_get_usage(usage, 'foo', None, self.srcdir, self.builddir)
        self.check_pkg_config('foo', None, {'cflags': ['-I' + incdir]})

        usage = self.make_usage('foo', include_path=['$srcdir/include'])
        self.check_usage(usage, include_path=[srcpathobj('include')])
        self.check_get_usage(usage, 'foo', None, self.srcdir, self.builddir)
        self.check_pkg_config('foo', None, {'cflags': ['-I' + incdir]})

    def test_include_path_builddir(self):
        incdir = os.path.join(self.builddir, 'include')
        usage = self.make_usage('foo', include_path='$builddir/include')
        self.check_usage(usage, include_path=[buildpathobj('include')])
        self.check_get_usage(usage, 'foo', None, self.srcdir, self.builddir)
        self.check_pkg_config('foo', None, {'cflags': ['-I' + incdir]})

        usage = self.make_usage('foo', include_path=['$builddir/include'])
        self.check_usage(usage, include_path=[buildpathobj('include')])
        self.check_get_usage(usage, 'foo', None, self.srcdir, self.builddir)
        self.check_pkg_config('foo', None, {'cflags': ['-I' + incdir]})

    def test_include_path_absolute(self):
        incdir = abspath('/path/to/include')
        usage = self.make_usage('foo', include_path='/path/to/include')
        self.check_usage(usage, include_path=[abspathobj('/path/to/include')])
        self.check_get_usage(usage, 'foo', None, self.srcdir, self.builddir)
        self.check_pkg_config('foo', None, {'cflags': ['-I' + incdir]})

        usage = self.make_usage('foo', include_path='/path/to/include')
        self.check_usage(usage, include_path=[abspathobj('/path/to/include')])
        self.check_get_usage(usage, 'foo', None, None, None)
        self.check_pkg_config('foo', None, {'cflags': ['-I' + incdir]})

    def test_invalid_include_path(self):
        with self.assertRaises(FieldError):
            self.make_usage('foo', include_path='../include')

    def test_library_path_relative(self):
        libdir = os.path.join(self.builddir, 'lib')
        usage = self.make_usage('foo', library_path='lib')
        self.check_usage(usage, library_path=[buildpathobj('lib')])
        self.check_get_usage(usage, 'foo', None, self.srcdir, self.builddir)
        self.check_pkg_config('foo', None, {'libs': ['-L' + libdir, '-lfoo']})

        usage = self.make_usage('foo', library_path=['lib'])
        self.check_usage(usage, library_path=[buildpathobj('lib')])
        self.check_get_usage(usage, 'foo', None, self.srcdir, self.builddir)
        self.check_pkg_config('foo', None, {'libs': ['-L' + libdir, '-lfoo']})

    def test_library_path_srcdir(self):
        libdir = os.path.join(self.srcdir, 'lib')
        usage = self.make_usage('foo', library_path='$srcdir/lib')
        self.check_usage(usage, library_path=[srcpathobj('lib')])
        self.check_get_usage(usage, 'foo', None, self.srcdir, self.builddir)
        self.check_pkg_config('foo', None, {'libs': ['-L' + libdir, '-lfoo']})

        usage = self.make_usage('foo', library_path=['$srcdir/lib'])
        self.check_usage(usage, library_path=[srcpathobj('lib')])
        self.check_get_usage(usage, 'foo', None, self.srcdir, self.builddir)
        self.check_pkg_config('foo', None, {'libs': ['-L' + libdir, '-lfoo']})

    def test_library_path_builddir(self):
        libdir = os.path.join(self.builddir, 'lib')
        usage = self.make_usage('foo', library_path='$builddir/lib')
        self.check_usage(usage, library_path=[buildpathobj('lib')])
        self.check_get_usage(usage, 'foo', None, self.srcdir, self.builddir)
        self.check_pkg_config('foo', None, {'libs': ['-L' + libdir, '-lfoo']})

        usage = self.make_usage('foo', library_path=['$builddir/lib'])
        self.check_usage(usage, library_path=[buildpathobj('lib')])
        self.check_get_usage(usage, 'foo', None, self.srcdir, self.builddir)
        self.check_pkg_config('foo', None, {'libs': ['-L' + libdir, '-lfoo']})

    def test_library_path_absolute(self):
        libdir = abspath('/path/to/lib')
        usage = self.make_usage('foo', library_path='/path/to/lib')
        self.check_usage(usage, library_path=[abspathobj('/path/to/lib')])
        self.check_get_usage(usage, 'foo', None, self.srcdir, self.builddir)
        self.check_pkg_config('foo', None, {'libs': ['-L' + libdir, '-lfoo']})

        usage = self.make_usage('foo', library_path='/path/to/lib')
        self.check_usage(usage, library_path=[abspathobj('/path/to/lib')])
        self.check_get_usage(usage, 'foo', None, None, None)
        self.check_pkg_config('foo', None, {'libs': ['-L' + libdir, '-lfoo']})

    def test_invalid_library_path(self):
        with self.assertRaises(FieldError):
            self.make_usage('foo', library_path='../lib')

    def test_headers(self):
        usage = self.make_usage('foo', headers='foo.hpp')
        self.check_usage(usage, headers=['foo.hpp'])
        self.check_get_usage(usage, 'foo', None, None, None, {
            'name': 'foo', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['foo'], 'requirements': {
                'auto_link': False, 'headers': ['foo.hpp'],
                'libraries': ['foo'],
            },
        })
        self.check_pkg_config('foo', None)

        usage = self.make_usage('foo', headers=['foo.hpp'])
        self.check_usage(usage, headers=['foo.hpp'])
        self.check_get_usage(usage, 'foo', None, None, None, {
            'name': 'foo', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['foo'], 'requirements': {
                'auto_link': False, 'headers': ['foo.hpp'],
                'libraries': ['foo'],
            },
        })
        self.check_pkg_config('foo', None)

    def test_libraries(self):
        usage = self.make_usage('foo', libraries='bar')
        self.check_usage(usage, libraries=['bar'])
        self.check_get_usage(usage, 'foo', None, None, None, {
            'name': 'foo', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['foo'], 'requirements': {
                'auto_link': False, 'headers': [], 'libraries': ['bar'],
            },
        })
        self.check_pkg_config('foo', None, {'libs': ['-lbar']})

        usage = self.make_usage('foo', libraries=['bar'])
        self.check_usage(usage, libraries=['bar'])
        self.check_get_usage(usage, 'foo', None, None, None, {
            'name': 'foo', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['foo'], 'requirements': {
                'auto_link': False, 'headers': [], 'libraries': ['bar'],
            },
        })
        self.check_pkg_config('foo', None, {'libs': ['-lbar']})

        usage = self.make_usage('foo', libraries=None)
        self.check_usage(usage, libraries=[])
        self.check_get_usage(usage, 'foo', None, None, None, {
            'name': 'foo', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['foo'], 'requirements': {
                'auto_link': False, 'headers': [], 'libraries': [],
            },
        })
        self.check_pkg_config('foo', None, {'libs': []})

        usage = self.make_usage('foo', libraries=[
            {'type': 'library', 'name': 'bar'},
        ])
        self.check_usage(usage, libraries=['bar'])
        self.check_get_usage(usage, 'foo', None, None, None, {
            'name': 'foo', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['foo'], 'requirements': {
                'auto_link': False, 'headers': [], 'libraries': ['bar'],
            },
        })
        self.check_pkg_config('foo', None, {'libs': ['-lbar']})

        usage = self.make_usage('foo', libraries=[
            {'type': 'guess', 'name': 'bar'},
        ])
        self.check_usage(usage, libraries=[{'type': 'guess', 'name': 'bar'}])
        self.check_get_usage(usage, 'foo', None, None, None, {
            'name': 'foo', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['foo'], 'requirements': {
                'auto_link': False, 'headers': [], 'libraries': ['bar'],
            },
        })
        self.check_pkg_config('foo', None, {'libs': ['-lbar']})

        usage = self.make_usage('foo', libraries=[
            {'type': 'framework', 'name': 'bar'},
        ])
        self.check_usage(usage, libraries=[
            {'type': 'framework', 'name': 'bar'},
        ])
        self.check_get_usage(usage, 'foo', None, None, None, {
            'name': 'foo', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['foo'], 'requirements': {
                'auto_link': False, 'headers': [], 'libraries': [],
            },
        })
        self.check_pkg_config('foo', None, {'libs': ['-framework', 'bar']})

    def test_compile_flags(self):
        usage = self.make_usage('foo', compile_flags='-pthread -fPIC')
        self.check_usage(usage, compile_flags=['-pthread', '-fPIC'])
        self.check_get_usage(usage, 'foo', None, None, None)
        self.check_pkg_config('foo', None, {'cflags': ['-pthread', '-fPIC']})

        usage = self.make_usage('foo', compile_flags=['-pthread', '-fPIC'])
        self.check_usage(usage, compile_flags=['-pthread', '-fPIC'])
        self.check_get_usage(usage, 'foo', None, None, None)
        self.check_pkg_config('foo', None, {'cflags': ['-pthread', '-fPIC']})

    def test_link_flags(self):
        usage = self.make_usage('foo', link_flags='-pthread -fPIC')
        self.check_usage(usage, link_flags=['-pthread', '-fPIC'])
        self.check_get_usage(usage, 'foo', None, None, None)
        self.check_pkg_config('foo', None, {
            'libs': ['-pthread', '-fPIC', '-lfoo'],
        })

        usage = self.make_usage('foo', link_flags=['-pthread', '-fPIC'])
        self.check_usage(usage, link_flags=['-pthread', '-fPIC'])
        self.check_get_usage(usage, 'foo', None, None, None)
        self.check_pkg_config('foo', None, {
            'libs': ['-pthread', '-fPIC', '-lfoo'],
        })

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        usage = self.make_usage('foo', submodules=submodules_required)
        self.check_usage(usage, libraries=[])
        self.check_get_usage(usage, 'foo', ['sub'], None, None, {
            'name': 'foo', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['foo[sub]'], 'requirements': {
                'auto_link': False, 'headers': [], 'libraries': ['foo_sub'],
            },
        })
        self.check_pkg_config('foo', ['sub'], {'libs': ['-lfoo_sub']})

        usage = self.make_usage('foo', libraries=['bar'],
                                submodules=submodules_required)
        self.check_usage(usage, libraries=['bar'])
        self.check_get_usage(usage, 'foo', ['sub'], None, None, {
            'name': 'foo', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['foo[sub]'], 'requirements': {
                'auto_link': False, 'headers': [],
                'libraries': ['bar', 'foo_sub'],
            },
        })
        self.check_pkg_config('foo', ['sub'], {'libs': ['-lbar', '-lfoo_sub']})

        usage = self.make_usage('foo', submodules=submodules_optional)
        self.check_usage(usage, libraries=[{'type': 'guess', 'name': 'foo'}])
        self.check_get_usage(usage, 'foo', ['sub'], None, None, {
            'name': 'foo', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['foo[sub]'], 'requirements': {
                'auto_link': False, 'headers': [],
                'libraries': ['foo', 'foo_sub'],
            },
        })
        self.check_pkg_config('foo', ['sub'], {'libs': ['-lfoo', '-lfoo_sub']})

        usage = self.make_usage('foo', libraries=['bar'],
                                submodules=submodules_optional)
        self.check_usage(usage, libraries=['bar'])
        self.check_get_usage(usage, 'foo', ['sub'], None, None, {
            'name': 'foo', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['foo[sub]'], 'requirements': {
                'auto_link': False, 'headers': [],
                'libraries': ['bar', 'foo_sub'],
            },
        })
        self.check_pkg_config('foo', ['sub'], {'libs': ['-lbar', '-lfoo_sub']})

    def test_submodule_map(self):
        submodules_required = {'names': '*', 'required': True}

        usage = self.make_usage('foo', submodule_map='$submodule',
                                submodules=submodules_required)
        self.check_usage(usage, libraries=[])
        self.check_get_usage(usage, 'foo', ['sub'], None, None, {
            'name': 'foo', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['foo[sub]'], 'requirements': {
                'auto_link': False, 'headers': [], 'libraries': ['sub'],
            },
        })
        self.check_pkg_config('foo', ['sub'], {'libs': ['-lsub']})

        usage = self.make_usage('foo', submodule_map={
            '*': {'libraries': '$submodule'},
        }, submodules=submodules_required)
        self.check_usage(usage, libraries=[])
        self.check_get_usage(usage, 'foo', ['sub'], None, None, {
            'name': 'foo', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['foo[sub]'], 'requirements': {
                'auto_link': False, 'headers': [], 'libraries': ['sub'],
            },
        })
        self.check_pkg_config('foo', ['sub'], {'libs': ['-lsub']})

        usage = self.make_usage('foo', submodule_map={'sub': {
            'include_path': '/sub/incdir',
            'library_path': '/sub/libdir',
            'headers': 'sub.hpp',
            'libraries': 'sublib',
            'compile_flags': '-Dsub',
            'link_flags': '-Wl,-sub',
        }, '*': {'libraries': '$submodule'}}, submodules=submodules_required)
        self.check_usage(usage, libraries=[])
        self.check_get_usage(usage, 'foo', ['sub'], None, None, {
            'name': 'foo', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['foo[sub]'], 'requirements': {
                'auto_link': False, 'headers': ['sub.hpp'],
                'libraries': ['sublib'],
            },
        })
        self.check_pkg_config('foo', ['sub'], {
            'cflags': ['-Dsub', '-I' + abspath('/sub/incdir')],
            'libs': ['-L' + abspath('/sub/libdir'), '-Wl,-sub', '-lsublib'],
        })
        self.check_get_usage(usage, 'foo', ['sub2'], None, None, {
            'name': 'foo', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['foo[sub2]'], 'requirements': {
                'auto_link': False, 'headers': [], 'libraries': ['sub2'],
            },
        })
        self.check_pkg_config('foo', ['sub2'], {'libs': ['-lsub2']})

        usage = self.make_usage('foo', submodule_map={
            'sub': {
                'include_path': '/incdir/$submodule',
                'library_path': '/libdir/$submodule',
                'headers': '$submodule/file.hpp',
                'libraries': '$submodule',
                'compile_flags': '-D$submodule',
                'link_flags': '-Wl,-$submodule',
            },
            '*': {
                'include_path': '/incdir/star/$submodule',
                'library_path': '/libdir/star/$submodule',
                'headers': 'star/$submodule/file.hpp',
                'libraries': 'star$submodule',
                'compile_flags': '-Dstar$submodule',
                'link_flags': '-Wl,-star$submodule',
            },
        }, submodules=submodules_required)
        self.check_usage(usage, libraries=[])
        self.check_get_usage(usage, 'foo', ['sub'], None, None, {
            'name': 'foo', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['foo[sub]'], 'requirements': {
                'auto_link': False, 'headers': ['sub/file.hpp'],
                'libraries': ['sub'],
            },
        })
        self.check_pkg_config('foo', ['sub'], {
            'cflags': ['-Dsub', '-I' + abspath('/incdir/sub')],
            'libs': ['-L' + abspath('/libdir/sub'), '-Wl,-sub', '-lsub'],
        })
        self.check_get_usage(usage, 'foo', ['sub2'], None, None, {
            'name': 'foo', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['foo[sub2]'], 'requirements': {
                'auto_link': False, 'headers': ['star/sub2/file.hpp'],
                'libraries': ['starsub2'],
            },
        })
        self.check_pkg_config('foo', ['sub2'], {
            'cflags': ['-Dstarsub2', '-I' + abspath('/incdir/star/sub2')],
            'libs': ['-L' + abspath('/libdir/star/sub2'), '-Wl,-starsub2',
                     '-lstarsub2'],
        })

    def test_boost(self):
        submodules = {'names': '*', 'required': False}
        for plat in ['linux', 'darwin', 'windows']:
            opts = {'target_platform': plat}
            usage = self.make_usage('boost', submodules=submodules,
                                    common_options=opts)
            self.check_usage(usage, auto_link=(plat == 'windows'),
                             headers=['boost/version.hpp'], libraries=[],
                             include_path=[], library_path=[])
            self.check_get_usage(usage, 'boost', None, None, None, {
                'name': 'boost', 'type': self.type, 'path': self.pkgconfdir,
                'pcfiles': ['boost'], 'requirements': {
                    'auto_link': plat == 'windows',
                    'headers': ['boost/version.hpp'], 'libraries': [],
                },
            })
            self.check_pkg_config('boost', None, {'libs': ''})
            self.check_get_usage(usage, 'boost', ['thread'], None, None, {
                'name': 'boost', 'type': self.type, 'path': self.pkgconfdir,
                'pcfiles': ['boost[thread]'], 'requirements': {
                    'auto_link': plat == 'windows',
                    'headers': ['boost/version.hpp'],
                    'libraries': ['boost_thread'] if plat != 'windows' else [],
                },
            })
            self.check_pkg_config('boost', ['thread'], {
                'cflags': ['-pthread'] if plat != 'windows' else [],
                'libs': ( (['-pthread'] if plat == 'linux' else []) +
                          (['-lboost_thread'] if plat != 'windows' else []) ),
            })

            usage = self.make_usage('boost', libraries=['boost'],
                                    submodules=submodules, common_options=opts)
            self.check_usage(usage, auto_link=(plat == 'windows'),
                             headers=['boost/version.hpp'],
                             libraries=['boost'], include_path=[],
                             library_path=[])
            self.check_get_usage(usage, 'boost', None, None, None, {
                'name': 'boost', 'type': self.type, 'path': self.pkgconfdir,
                'pcfiles': ['boost'], 'requirements': {
                    'auto_link': plat == 'windows',
                    'headers': ['boost/version.hpp'], 'libraries': ['boost'],
                },
            })
            self.check_pkg_config('boost', None)
            extra_libs = ['boost_regex'] if plat != 'windows' else []
            self.check_get_usage(usage, 'boost', ['regex'], None, None, {
                'name': 'boost', 'type': self.type, 'path': self.pkgconfdir,
                'pcfiles': ['boost[regex]'], 'requirements': {
                    'auto_link': plat == 'windows',
                    'headers': ['boost/version.hpp'],
                    'libraries': ['boost'] + extra_libs,
                },
            })
            self.check_pkg_config('boost', ['regex'], {
                'libs': ['-l' + i for i in ['boost'] + extra_libs],
            })

    def test_boost_env_vars(self):
        submodules = {'names': '*', 'required': False}
        boost_root = abspath('/boost')
        boost_inc = abspath('/boost/inc')
        boost_lib = abspath('/boost/lib')
        opts = {'target_platform': 'linux', 'env': {
            'BOOST_ROOT': boost_root,
            'BOOST_INCLUDEDIR': boost_inc,
        }}
        pathobjs = {
            'include_path': [abspathobj(boost_inc)],
            'library_path': [abspathobj(boost_lib)],
        }

        usage = self.make_usage('boost', submodules=submodules,
                                common_options=opts)
        self.check_usage(usage, auto_link=False,
                         headers=['boost/version.hpp'], libraries=[],
                         **pathobjs)
        self.check_get_usage(usage, 'boost', None, None, None, {
            'name': 'boost', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['boost'], 'requirements': {
                'auto_link': False, 'headers': ['boost/version.hpp'],
                'libraries': [],
            },
        })
        self.check_pkg_config('boost', None, {
            'cflags': ['-I{}'.format(boost_inc)],
            'libs': ['-L{}'.format(boost_lib)],
        })
        self.check_get_usage(usage, 'boost', ['thread'], None, None, {
            'name': 'boost', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['boost[thread]'], 'requirements': {
                'auto_link': False, 'headers': ['boost/version.hpp'],
                'libraries': ['boost_thread'],
            },
        })
        self.check_pkg_config('boost', ['thread'], {
            'cflags': ['-I{}'.format(boost_inc), '-pthread'],
            'libs': ['-L{}'.format(boost_lib), '-pthread', '-lboost_thread'],
        })

        usage = self.make_usage('boost', libraries=['boost'],
                                submodules=submodules, common_options=opts)
        self.check_usage(usage, auto_link=False,
                         headers=['boost/version.hpp'], libraries=['boost'],
                         **pathobjs)
        self.check_get_usage(usage, 'boost', None, None, None, {
            'name': 'boost', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['boost'], 'requirements': {
                'auto_link': False, 'headers': ['boost/version.hpp'],
                'libraries': ['boost'],
            },
        })
        self.check_pkg_config('boost', None, {
            'cflags': ['-I{}'.format(boost_inc)],
            'libs': ['-L{}'.format(boost_lib), '-lboost'],
        })
        self.check_get_usage(usage, 'boost', ['regex'], None, None, {
            'name': 'boost', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['boost[regex]'], 'requirements': {
                'auto_link': False, 'headers': ['boost/version.hpp'],
                'libraries': ['boost', 'boost_regex'],
            },
        })
        self.check_pkg_config('boost', ['regex'], {
            'cflags': ['-I{}'.format(boost_inc)],
            'libs': ['-L{}'.format(boost_lib), '-lboost', '-lboost_regex'],
        })

    def test_target_platform(self):
        usage = self.make_usage('gl', common_options={
            'target_platform': 'linux',
        })
        self.check_usage(usage, libraries=[{'type': 'guess', 'name': 'gl'}])
        self.check_get_usage(usage, 'gl', None, None, None, {
            'name': 'gl', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['gl'], 'requirements': {
                'auto_link': False, 'headers': [], 'libraries': ['GL'],
            },
        })
        self.check_pkg_config('gl', None, {'libs': ['-lGL']})

        usage = self.make_usage('gl', common_options={
            'target_platform': 'darwin',
        })
        self.check_usage(usage, libraries=[{'type': 'guess', 'name': 'gl'}])
        self.check_get_usage(usage, 'gl', None, None, None, {
            'name': 'gl', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['gl'], 'requirements': {
                'auto_link': False, 'headers': [], 'libraries': [],
            },
        })
        self.check_pkg_config('gl', None, {'libs': ['-framework', 'OpenGL']})

        usage = self.make_usage('gl', libraries=['gl'], common_options={
            'target_platform': 'linux',
        })
        self.check_usage(usage, libraries=['gl'])
        self.check_get_usage(usage, 'gl', None, None, None)
        self.check_pkg_config('gl', None)

        usage = self.make_usage(
            'foo', libraries=[{'type': 'guess', 'name': 'gl'}],
            common_options={'target_platform': 'linux'}
        )
        self.check_usage(usage, libraries=[{'type': 'guess', 'name': 'gl'}])
        self.check_get_usage(usage, 'foo', None, None, None, {
            'name': 'foo', 'type': self.type, 'path': self.pkgconfdir,
            'pcfiles': ['foo'], 'requirements': {
                'auto_link': False, 'headers': [], 'libraries': ['GL'],
            },
        })
        self.check_pkg_config('foo', None, {'libs': ['-lGL']})

    def test_rehydrate(self):
        opts = self.make_options()
        path_bases = ('srcdir', 'builddir')
        usage = self.usage_type('foo', submodules=None, _options=opts,
                                _path_bases=path_bases)
        data = usage.dehydrate()
        self.assertEqual(usage, Usage.rehydrate(data, _options=opts))

        usage = self.usage_type('foo', submodules=None,
                                compile_flags=['compile'], link_flags=['link'],
                                _options=opts, _path_bases=path_bases)
        data = through_json(usage.dehydrate())
        self.assertEqual(usage, Usage.rehydrate(data, _options=opts))

        submodules = {'names': '*', 'required': False}
        usage = self.usage_type('foo', submodules=submodules, submodule_map={
            'foosub': {
                'include_path': 'include',
                'library_path': 'lib',
            },
            'barsub': {
                'compile_flags': 'compile',
                'link_flags': 'link',
            },
        }, _options=opts, _path_bases=path_bases)
        data = through_json(usage.dehydrate())
        self.assertEqual(usage, Usage.rehydrate(data, _options=opts))

    def test_upgrade(self):
        opts = self.make_options()
        data = {'type': self.type, '_version': 0, 'include_path': [],
                'library_path': [], 'compile_flags': [], 'link_flags': []}
        with mock.patch.object(self.usage_type, 'upgrade',
                               side_effect=self.usage_type.upgrade) as m:
            pkg = Usage.rehydrate(data, _options=opts)
            self.assertIsInstance(pkg, self.usage_type)
            m.assert_called_once()

    def test_invalid_usage(self):
        with self.assertRaises(FieldError):
            self.make_usage('foo', include_path='$builddir/include',
                            _path_bases=('srcdir',))

        with self.assertRaises(FieldError):
            self.make_usage('foo', library_path='$srcdir/lib',
                            _path_bases=('builddir',))

        with self.assertRaises(FieldError):
            self.make_usage('foo', include_path='include', _path_bases=())


class TestSystem(TestPath):
    usage_type = SystemUsage
    type = 'system'

    def asetUp(self):
        self.mock_run = mock.patch('subprocess.run', side_effect=OSError())
        self.mock_run.start()
        super().setUp()

    def atearDown(self):
        super().tearDown()
        self.mock_run.stop()

    def check_get_usage(self, *args, find_pkg_config=False, **kwargs):
        side_effect = None if find_pkg_config else OSError()
        with mock.patch('subprocess.run', side_effect=side_effect):
            super().check_get_usage(*args, **kwargs)

    def test_pkg_config(self):
        usage = self.make_usage('foo')
        self.check_usage(usage)
        with mock.patch('subprocess.run'):
            self.check_get_usage(usage, 'foo', None, None, None, {
                'name': 'foo', 'type': 'system', 'path': None,
                'pcfiles': ['foo'], 'extra_args': [],
            }, find_pkg_config=True)
