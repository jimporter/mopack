from . import MockPackage, UsageTest

from mopack.types import FieldError
from mopack.path import Path
from mopack.usage import make_usage
from mopack.usage.pkg_config import PkgConfigUsage


class TestMakeUsage(UsageTest):
    path_bases = ('srcdir', 'builddir')

    def setUp(self):
        self.pkg = MockPackage(
            'foo', srcdir=self.srcdir, builddir=self.builddir,
            _options=self.make_options()
        )

    def test_make(self):
        usage = make_usage(self.pkg, {'type': 'pkg_config',
                                      'pkg_config_path': 'path'})
        self.assertIsInstance(usage, PkgConfigUsage)
        self.assertEqual(usage.pkg_config_path, [Path('path', 'builddir')])

    def test_make_string(self):
        usage = make_usage(self.pkg, 'pkg_config')
        self.assertIsInstance(usage, PkgConfigUsage)
        self.assertEqual(usage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])

    def test_unknown_usage(self):
        with self.assertRaises(FieldError):
            make_usage(self.pkg, {'type': 'goofy'})

    def test_no_usage(self):
        with self.assertRaises(TypeError):
            make_usage(self.pkg, None)

    def test_invalid_keys(self):
        with self.assertRaises(TypeError):
            make_usage(self.pkg, {'type': 'pkg_config', 'unknown': 'blah'})

    def test_invalid_values(self):
        with self.assertRaises(FieldError):
            make_usage(self.pkg, {'type': 'pkg_config',
                                  'pkg_config_path': '..'})
