from os.path import abspath

from . import through_json, UsageTest

from mopack.path import Path
from mopack.shell import ShellArguments
from mopack.types import FieldError
from mopack.usage import Usage
from mopack.usage.pkg_config import PkgConfigUsage


class TestPkgConfig(UsageTest):
    usage_type = PkgConfigUsage

    def test_basic(self):
        usage = self.make_usage('foo')
        self.assertEqual(usage.path, Path('builddir', 'pkgconfig'))
        self.assertEqual(usage.pcfile, 'foo')
        self.assertEqual(usage.extra_args, ShellArguments())
        self.assertEqual(usage.get_usage(None, None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['foo'], 'extra_args': [],
        })

    def test_path_relative(self):
        usage = self.make_usage('foo', path='pkgconf')
        self.assertEqual(usage.path, Path('builddir', 'pkgconf'))
        self.assertEqual(usage.pcfile, 'foo')
        self.assertEqual(usage.extra_args, ShellArguments())
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconf'),
            'pcfiles': ['foo'], 'extra_args': [],
        })

    def test_path_srcdir(self):
        usage = self.make_usage('foo', path='$srcdir/pkgconf')
        self.assertEqual(usage.path, Path('srcdir', 'pkgconf'))
        self.assertEqual(usage.pcfile, 'foo')
        self.assertEqual(usage.extra_args, ShellArguments())
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/srcdir/pkgconf'),
            'pcfiles': ['foo'], 'extra_args': [],
        })

    def test_path_builddir(self):
        usage = self.make_usage('foo', path='$builddir/pkgconf')
        self.assertEqual(usage.path, Path('builddir', 'pkgconf'))
        self.assertEqual(usage.pcfile, 'foo')
        self.assertEqual(usage.extra_args, ShellArguments())
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconf'),
            'pcfiles': ['foo'], 'extra_args': [],
        })

    def test_extra_args(self):
        usage = self.make_usage('foo', path='pkgconf', extra_args='--static')
        self.assertEqual(usage.path, Path('builddir', 'pkgconf'))
        self.assertEqual(usage.pcfile, 'foo')
        self.assertEqual(usage.extra_args, ShellArguments(['--static']))
        self.assertEqual(usage.get_usage(None, None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconf'),
            'pcfiles': ['foo'], 'extra_args': ['--static'],
        })

        usage = self.make_usage('foo', path='pkgconf', extra_args=['--static'])
        self.assertEqual(usage.path, Path('builddir', 'pkgconf'))
        self.assertEqual(usage.pcfile, 'foo')
        self.assertEqual(usage.extra_args, ShellArguments(['--static']))
        self.assertEqual(usage.get_usage(None, None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconf'),
            'pcfiles': ['foo'], 'extra_args': ['--static'],
        })

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        usage = self.make_usage('foo', submodules=submodules_required)
        self.assertEqual(usage.path, Path('builddir', 'pkgconfig'))
        self.assertEqual(usage.pcfile, None)
        self.assertEqual(usage.extra_args, ShellArguments())
        self.assertEqual(usage.get_usage(['sub'], None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['foo_sub'], 'extra_args': [],
        })

        usage = self.make_usage('foo', pcfile='bar',
                                submodules=submodules_required)
        self.assertEqual(usage.path, Path('builddir', 'pkgconfig'))
        self.assertEqual(usage.pcfile, 'bar')
        self.assertEqual(usage.extra_args, ShellArguments())
        self.assertEqual(usage.get_usage(['sub'], None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['bar', 'foo_sub'], 'extra_args': [],
        })

        usage = self.make_usage('foo', submodules=submodules_optional)
        self.assertEqual(usage.path, Path('builddir', 'pkgconfig'))
        self.assertEqual(usage.pcfile, 'foo')
        self.assertEqual(usage.extra_args, ShellArguments())
        self.assertEqual(usage.get_usage(['sub'], None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['foo', 'foo_sub'], 'extra_args': [],
        })

        usage = self.make_usage('foo', pcfile='bar',
                                submodules=submodules_optional)
        self.assertEqual(usage.path, Path('builddir', 'pkgconfig'))
        self.assertEqual(usage.pcfile, 'bar')
        self.assertEqual(usage.extra_args, ShellArguments())
        self.assertEqual(usage.get_usage(['sub'], None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['bar', 'foo_sub'], 'extra_args': [],
        })

    def test_submodule_map(self):
        submodules_required = {'names': '*', 'required': True}

        usage = self.make_usage('foo', submodule_map='$submodule',
                                submodules=submodules_required)
        self.assertEqual(usage.path, Path('builddir', 'pkgconfig'))
        self.assertEqual(usage.pcfile, None)
        self.assertEqual(usage.extra_args, ShellArguments())
        self.assertEqual(usage.get_usage(['sub'], None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['sub'], 'extra_args': [],
        })

        usage = self.make_usage('foo', submodule_map={
            '*': {'pcfile': '$submodule'}
        }, submodules=submodules_required)
        self.assertEqual(usage.path, Path('builddir', 'pkgconfig'))
        self.assertEqual(usage.pcfile, None)
        self.assertEqual(usage.extra_args, ShellArguments())
        self.assertEqual(usage.get_usage(['sub'], None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['sub'], 'extra_args': [],
        })

        usage = self.make_usage('foo', submodule_map={
            'sub': {'pcfile': 'foopc'},
            'sub2': {'pcfile': '${{ submodule }}pc'},
            '*': {'pcfile': 'star${{ submodule }}pc'},
        }, submodules=submodules_required)
        self.assertEqual(usage.path, Path('builddir', 'pkgconfig'))
        self.assertEqual(usage.pcfile, None)
        self.assertEqual(usage.extra_args, ShellArguments())
        self.assertEqual(usage.get_usage(['sub'], None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['foopc'], 'extra_args': [],
        })
        self.assertEqual(usage.get_usage(['sub2'], None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['sub2pc'], 'extra_args': [],
        })
        self.assertEqual(usage.get_usage(['subfoo'], None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['starsubfoopc'], 'extra_args': [],
        })

        submodules = {'names': '*', 'required': False}
        usage = self.make_usage('foo', submodule_map={
            'sub': {'pcfile': 'subpc'},
            'sub2': {'pcfile': None},
        }, submodules=submodules)
        self.assertEqual(usage.path, Path('builddir', 'pkgconfig'))
        self.assertEqual(usage.pcfile, 'foo')
        self.assertEqual(usage.extra_args, ShellArguments())
        self.assertEqual(usage.get_usage(['sub'], None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['foo', 'subpc'], 'extra_args': [],
        })
        self.assertEqual(usage.get_usage(['sub2'], None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['foo'], 'extra_args': [],
        })

    def test_boost(self):
        submodules = {'names': '*', 'required': False}
        final_usage = {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['boost'], 'extra_args': [],
        }

        usage = self.make_usage('boost', submodules=submodules)
        self.assertEqual(usage.path, Path('builddir', 'pkgconfig'))
        self.assertEqual(usage.pcfile, 'boost')
        self.assertEqual(usage.get_usage(None, None, '/builddir'), final_usage)
        self.assertEqual(usage.get_usage(['thread'], None, '/builddir'),
                         final_usage)

        usage = self.make_usage('boost', submodule_map='boost_$submodule',
                                submodules=submodules)
        self.assertEqual(usage.path, Path('builddir', 'pkgconfig'))
        self.assertEqual(usage.pcfile, 'boost')
        self.assertEqual(usage.get_usage(None, None, '/builddir'), final_usage)
        self.assertEqual(usage.get_usage(['thread'], None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['boost', 'boost_thread'], 'extra_args': [],
        })

    def test_rehydrate(self):
        opts = self.make_options()
        path_bases = ('srcdir', 'builddir')
        usage = PkgConfigUsage('foo', submodules=None, _options=opts,
                               _path_bases=path_bases)
        data = through_json(usage.dehydrate())
        self.assertEqual(usage, Usage.rehydrate(data, _options=opts))

        usage = PkgConfigUsage('foo', submodules=None, extra_args=['foo'],
                               _options=opts, _path_bases=path_bases)
        data = through_json(usage.dehydrate())
        self.assertEqual(usage, Usage.rehydrate(data, _options=opts))

    def test_invalid_usage(self):
        with self.assertRaises(FieldError):
            self.make_usage('foo', path='$srcdir/pkgconf',
                            _path_bases=('builddir',))

        with self.assertRaises(FieldError):
            self.make_usage('foo', path='$builddir/pkgconf',
                            _path_bases=('srcdir',))

        with self.assertRaises(FieldError):
            self.make_usage('foo', _path_bases=())
