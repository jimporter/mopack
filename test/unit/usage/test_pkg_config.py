from os.path import abspath

from . import UsageTest

from mopack.usage.pkg_config import PkgConfigUsage


class TestPkgConfig(UsageTest):
    usage_type = PkgConfigUsage

    def test_basic(self):
        usage = self.make_usage('foo')
        self.assertEqual(usage.path, 'pkgconfig')
        self.assertEqual(usage.pcfile, 'foo')
        self.assertEqual(usage.get_usage(None, None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['foo'], 'extra_args': [],
        })

    def test_path(self):
        usage = self.make_usage('foo', path='pkgconf')
        self.assertEqual(usage.path, 'pkgconf')
        self.assertEqual(usage.pcfile, 'foo')
        self.assertEqual(usage.get_usage(None, None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconf'),
            'pcfiles': ['foo'], 'extra_args': [],
        })

    def test_extra_args(self):
        usage = self.make_usage('foo', path='pkgconf', extra_args='--static')
        self.assertEqual(usage.path, 'pkgconf')
        self.assertEqual(usage.pcfile, 'foo')
        self.assertEqual(usage.get_usage(None, None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconf'),
            'pcfiles': ['foo'], 'extra_args': ['--static'],
        })

        usage = self.make_usage('foo', path='pkgconf', extra_args=['--static'])
        self.assertEqual(usage.path, 'pkgconf')
        self.assertEqual(usage.pcfile, 'foo')
        self.assertEqual(usage.get_usage(None, None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconf'),
            'pcfiles': ['foo'], 'extra_args': ['--static'],
        })

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        usage = self.make_usage('foo', submodules=submodules_required)
        self.assertEqual(usage.path, 'pkgconfig')
        self.assertEqual(usage.pcfile, None)
        self.assertEqual(usage.get_usage(['sub'], None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['foo_sub'], 'extra_args': [],
        })

        usage = self.make_usage('foo', pcfile='bar',
                                submodules=submodules_required)
        self.assertEqual(usage.path, 'pkgconfig')
        self.assertEqual(usage.pcfile, 'bar')
        self.assertEqual(usage.get_usage(['sub'], None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['bar', 'foo_sub'], 'extra_args': [],
        })

        usage = self.make_usage('foo', submodules=submodules_optional)
        self.assertEqual(usage.path, 'pkgconfig')
        self.assertEqual(usage.pcfile, 'foo')
        self.assertEqual(usage.get_usage(['sub'], None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['foo', 'foo_sub'], 'extra_args': [],
        })

        usage = self.make_usage('foo', pcfile='bar',
                                submodules=submodules_optional)
        self.assertEqual(usage.path, 'pkgconfig')
        self.assertEqual(usage.pcfile, 'bar')
        self.assertEqual(usage.get_usage(['sub'], None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['bar', 'foo_sub'], 'extra_args': [],
        })

    def test_submodule_map(self):
        submodules_required = {'names': '*', 'required': True}

        usage = self.make_usage('foo', submodule_map='{submodule}',
                                submodules=submodules_required)
        self.assertEqual(usage.path, 'pkgconfig')
        self.assertEqual(usage.pcfile, None)
        self.assertEqual(usage.get_usage(['sub'], None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['sub'], 'extra_args': [],
        })

        usage = self.make_usage('foo', submodule_map={
            '*': {'pcfile': '{submodule}'}
        }, submodules=submodules_required)
        self.assertEqual(usage.path, 'pkgconfig')
        self.assertEqual(usage.pcfile, None)
        self.assertEqual(usage.get_usage(['sub'], None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['sub'], 'extra_args': [],
        })

        usage = self.make_usage('foo', submodule_map={
            'sub': {'pcfile': 'subpc'},
            '*': {'pcfile': '{submodule}'},
        }, submodules=submodules_required)
        self.assertEqual(usage.path, 'pkgconfig')
        self.assertEqual(usage.pcfile, None)
        self.assertEqual(usage.get_usage(['sub'], None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['subpc'], 'extra_args': [],
        })
        self.assertEqual(usage.get_usage(['sub2'], None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['sub2'], 'extra_args': [],
        })

    def test_boost(self):
        submodules = {'names': '*', 'required': False}
        final_usage = {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['boost'], 'extra_args': [],
        }

        usage = self.make_usage('boost', submodules=submodules)
        self.assertEqual(usage.path, 'pkgconfig')
        self.assertEqual(usage.pcfile, 'boost')
        self.assertEqual(usage.get_usage(None, None, '/builddir'), final_usage)
        self.assertEqual(usage.get_usage(['thread'], None, '/builddir'),
                         final_usage)

        usage = self.make_usage('boost', submodule_map='boost_{submodule}',
                                submodules=submodules)
        self.assertEqual(usage.path, 'pkgconfig')
        self.assertEqual(usage.pcfile, 'boost')
        self.assertEqual(usage.get_usage(None, None, '/builddir'), final_usage)
        self.assertEqual(usage.get_usage(['thread'], None, '/builddir'), {
            'type': 'pkg-config', 'path': abspath('/builddir/pkgconfig'),
            'pcfiles': ['boost', 'boost_thread'], 'extra_args': [],
        })

    def test_invalid(self):
        usage = self.make_usage('foo')
        with self.assertRaises(ValueError):
            usage.get_usage(None, None, None)
