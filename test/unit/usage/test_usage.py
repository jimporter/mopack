from . import UsageTest

from mopack.types import FieldError
from mopack.path import Path
from mopack.usage import make_usage
from mopack.usage.pkg_config import PkgConfigUsage


class TestMakeUsage(UsageTest):
    path_bases = ('srcdir', 'builddir')

    def test_make(self):
        usage = make_usage('pkg', {'type': 'pkg-config', 'path': 'path'},
                           submodules=None, _options=self.make_options(),
                           _path_bases=self.path_bases)
        self.assertIsInstance(usage, PkgConfigUsage)
        self.assertEqual(usage.path, Path('builddir', 'path'))

    def test_make_string(self):
        usage = make_usage('pkg', 'pkg-config', submodules=None,
                           _options=self.make_options(),
                           _path_bases=self.path_bases)
        self.assertIsInstance(usage, PkgConfigUsage)
        self.assertEqual(usage.path, Path('builddir', 'pkgconfig'))

    def test_unknown_usage(self):
        with self.assertRaises(FieldError):
            make_usage('pkg', {'type': 'goofy'}, submodules=None,
                       _options=self.make_options(),
                       _path_bases=self.path_bases)

    def test_no_usage(self):
        with self.assertRaises(TypeError):
            make_usage('pkg', None, submodules=None,
                       _options=self.make_options(),
                       _path_bases=self.path_bases)

    def test_invalid_keys(self):
        with self.assertRaises(TypeError):
            make_usage('pkg', {'type': 'pkg-config', 'unknown': 'blah'},
                       submodules=None, _options=self.make_options(),
                       _path_bases=self.path_bases)

    def test_invalid_values(self):
        with self.assertRaises(FieldError):
            make_usage('pkg', {'type': 'pkg-config', 'path': '..'},
                       submodules=None, _options=self.make_options(),
                       _path_bases=self.path_bases)
