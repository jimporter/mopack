import yaml
from unittest import TestCase
from yaml.error import MarkedYAMLError

from mopack.yaml_tools import SafeLineLoader
from mopack.sources import make_package
from mopack.sources.sdist import DirectoryPackage


class TestMakePackage(TestCase):
    def test_make(self):
        pkg = make_package('foo', {
            'source': 'directory', 'path': '/path', 'build': 'bfg9000',
            'config_file': '/path/to/mopack.yml'
        })
        self.assertIsInstance(pkg, DirectoryPackage)
        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.config_file, '/path/to/mopack.yml')
        self.assertEqual(pkg.path, '/path')
        self.assertEqual(pkg.builder.type, 'bfg9000')

    def test_invalid(self):
        self.assertRaises(TypeError, make_package, 'foo',
                          {'source': 'directory'})

    def test_invalid_marked(self):
        data = yaml.load('source: directory', Loader=SafeLineLoader)
        self.assertRaises(MarkedYAMLError, make_package, 'foo', data)

    def test_unknown(self):
        self.assertRaises(ValueError, make_package, 'foo', {'source': 'goofy'})
