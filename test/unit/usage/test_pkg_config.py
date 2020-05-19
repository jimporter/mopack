from . import UsageTest

from mopack.usage.pkg_config import PkgConfigUsage


class TestPkgConfig(UsageTest):
    usage_type = PkgConfigUsage

    def test_basic(self):
        usage = self.make_usage('foo')
        self.assertEqual(usage.path, 'pkgconfig')
        self.assertEqual(usage.usage(None, '/builddir'), {
            'type': 'pkg-config', 'path': '/builddir/pkgconfig'
        })

    def test_path(self):
        usage = self.make_usage('foo', path='pkgconf')
        self.assertEqual(usage.path, 'pkgconf')
        self.assertEqual(usage.usage(None, '/builddir'), {
            'type': 'pkg-config', 'path': '/builddir/pkgconf'
        })

    def test_invalid(self):
        usage = self.make_usage('foo')
        with self.assertRaises(ValueError):
            usage.usage(None, None)
