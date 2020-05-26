from . import UsageTest

from mopack.usage.pkg_config import PkgConfigUsage


class TestPkgConfig(UsageTest):
    usage_type = PkgConfigUsage

    def test_basic(self):
        usage = self.make_usage('foo')
        self.assertEqual(usage.path, 'pkgconfig')
        self.assertEqual(usage.pcfile, 'foo')
        self.assertEqual(usage.get_usage(None, None, '/builddir'), {
            'type': 'pkg-config', 'path': '/builddir/pkgconfig',
            'pcfiles': ['foo']
        })

    def test_path(self):
        usage = self.make_usage('foo', path='pkgconf')
        self.assertEqual(usage.path, 'pkgconf')
        self.assertEqual(usage.pcfile, 'foo')
        self.assertEqual(usage.get_usage(None, None, '/builddir'), {
            'type': 'pkg-config', 'path': '/builddir/pkgconf',
            'pcfiles': ['foo']
        })

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        usage = self.make_usage('foo', submodules=submodules_required)
        self.assertEqual(usage.path, 'pkgconfig')
        self.assertEqual(usage.pcfile, None)
        self.assertEqual(usage.get_usage(['sub'], None, '/builddir'), {
            'type': 'pkg-config', 'path': '/builddir/pkgconfig',
            'pcfiles': ['foo_sub'],
        })

        usage = self.make_usage('foo', pcfile='bar',
                                submodules=submodules_required)
        self.assertEqual(usage.path, 'pkgconfig')
        self.assertEqual(usage.pcfile, 'bar')
        self.assertEqual(usage.get_usage(['sub'], None, '/builddir'), {
            'type': 'pkg-config', 'path': '/builddir/pkgconfig',
            'pcfiles': ['bar', 'foo_sub'],
        })

        usage = self.make_usage('foo', submodules=submodules_optional)
        self.assertEqual(usage.path, 'pkgconfig')
        self.assertEqual(usage.pcfile, 'foo')
        self.assertEqual(usage.get_usage(['sub'], None, '/builddir'), {
            'type': 'pkg-config', 'path': '/builddir/pkgconfig',
            'pcfiles': ['foo', 'foo_sub'],
        })

        usage = self.make_usage('foo', pcfile='bar',
                                submodules=submodules_optional)
        self.assertEqual(usage.path, 'pkgconfig')
        self.assertEqual(usage.pcfile, 'bar')
        self.assertEqual(usage.get_usage(['sub'], None, '/builddir'), {
            'type': 'pkg-config', 'path': '/builddir/pkgconfig',
            'pcfiles': ['bar', 'foo_sub'],
        })

    def test_boost(self):
        submodules = {'names': '*', 'required': False}
        final_usage = {'type': 'pkg-config', 'path': '/builddir/pkgconfig',
                       'pcfiles': ['boost']}

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
        self.assertEqual(usage.get_usage(['thread'], None, '/builddir'),
                         {'type': 'pkg-config', 'path': '/builddir/pkgconfig',
                          'pcfiles': ['boost', 'boost_thread']})

    def test_invalid(self):
        usage = self.make_usage('foo')
        with self.assertRaises(ValueError):
            usage.get_usage(None, None, None)
