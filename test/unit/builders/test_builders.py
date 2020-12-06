from . import BuilderTest

from mopack.builders import make_builder
from mopack.builders.bfg9000 import Bfg9000Builder
from mopack.types import FieldError


class TestMakeBuilder(BuilderTest):
    def test_make(self):
        builder = make_builder('foo', {'type': 'bfg9000'}, submodules=None,
                               _options=self.make_options())
        self.assertIsInstance(builder, Bfg9000Builder)
        self.assertEqual(builder.name, 'foo')

    def test_make_string(self):
        builder = make_builder('foo', 'bfg9000', submodules=None,
                               _options=self.make_options())
        self.assertIsInstance(builder, Bfg9000Builder)
        self.assertEqual(builder.name, 'foo')

    def test_unknown_builder(self):
        self.assertRaises(FieldError, make_builder, 'foo', {'type': 'goofy'},
                          submodules=None, _options=self.make_options())

    def test_invalid_keys(self):
        self.assertRaises(TypeError, make_builder, 'foo',
                          {'type': 'bfg9000', 'unknown': 'blah'},
                          submodules=None, _options=self.make_options())

    def test_invalid_values(self):
        self.assertRaises(FieldError, make_builder, 'foo',
                          {'type': 'bfg9000', 'extra_args': 1},
                          submodules=None, _options=self.make_options())
