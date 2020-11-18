from unittest import TestCase

from mopack.usage import make_usage
from mopack.usage.pkg_config import PkgConfigUsage
from mopack.types import FieldError


class TestMakeUsage(TestCase):
    def test_make(self):
        usage = make_usage('pkg', {'type': 'pkg-config', 'path': 'path'},
                           submodules=None)
        self.assertIsInstance(usage, PkgConfigUsage)
        self.assertEqual(usage.path, 'path')

    def test_make_string(self):
        usage = make_usage('pkg', 'pkg-config', submodules=None)
        self.assertIsInstance(usage, PkgConfigUsage)
        self.assertEqual(usage.path, 'pkgconfig')

    def test_unknown_usage(self):
        self.assertRaises(FieldError, make_usage, 'pkg', {'type': 'goofy'},
                          submodules=None)

    def test_invalid_keys(self):
        self.assertRaises(TypeError, make_usage, 'pkg',
                          {'type': 'pkg-config', 'unknown': 'blah'},
                          submodules=None)

    def test_invalid_values(self):
        self.assertRaises(FieldError, make_usage, 'pkg',
                          {'type': 'pkg-config', 'path': '..'},
                          submodules=None)
