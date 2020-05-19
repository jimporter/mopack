import yaml
from unittest import TestCase
from yaml.error import MarkedYAMLError

from mopack.yaml_tools import SafeLineLoader
from mopack.usage import make_usage
from mopack.usage.pkg_config import PkgConfigUsage


class TestMakeUsage(TestCase):
    def test_make(self):
        usage = make_usage('pkg', {'type': 'pkg-config', 'path': 'path'})
        self.assertIsInstance(usage, PkgConfigUsage)
        self.assertEqual(usage.path, 'path')

    def test_make_string(self):
        usage = make_usage('pkg', 'pkg-config')
        self.assertIsInstance(usage, PkgConfigUsage)
        self.assertEqual(usage.path, 'pkgconfig')

    def test_invalid(self):
        self.assertRaises(TypeError, make_usage, 'pkg',
                          {'type': 'pkg-config', 'path': '..'})

    def test_invalid_marked(self):
        data = yaml.load('type: pkg-config\npath: ..',
                         Loader=SafeLineLoader)
        self.assertRaises(MarkedYAMLError, make_usage, 'pkg', data)

    def test_unknown(self):
        self.assertRaises(ValueError, make_usage, 'pkg', {'type': 'goofy'})
