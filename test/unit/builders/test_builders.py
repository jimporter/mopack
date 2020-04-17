import yaml
from unittest import TestCase
from yaml.error import MarkedYAMLError

from mopack.yaml_tools import SafeLineLoader
from mopack.builders import make_builder
from mopack.builders.bfg9000 import Bfg9000Builder


class TestMakeBuilder(TestCase):
    def test_make(self):
        builder = make_builder('foo', {'type': 'bfg9000'})
        self.assertIsInstance(builder, Bfg9000Builder)
        self.assertEqual(builder.name, 'foo')

    def test_make_string(self):
        builder = make_builder('foo', 'bfg9000')
        self.assertIsInstance(builder, Bfg9000Builder)
        self.assertEqual(builder.name, 'foo')

    def test_invalid(self):
        self.assertRaises(TypeError, make_builder, 'foo',
                          {'type': 'bfg9000', 'builddir': '..'})

    def test_invalid_marked(self):
        data = yaml.load('type: bfg9000\nbuilddir: ..', Loader=SafeLineLoader)
        self.assertRaises(MarkedYAMLError, make_builder, 'foo', data)

    def test_unknown(self):
        self.assertRaises(ValueError, make_builder, 'foo', {'type': 'goofy'})
