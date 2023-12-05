from . import BuilderTest, MockPackage

from mopack.builders import make_builder
from mopack.builders.bfg9000 import Bfg9000Builder
from mopack.options import ExprSymbols
from mopack.types import FieldError


class TestMakeBuilder(BuilderTest):
    symbols = ExprSymbols(variable='foo').augment_path_bases('srcdir')

    def setUp(self):
        self.pkg = MockPackage('foo', _options=self.make_options())

    def test_make(self):
        builder = make_builder(self.pkg, {'type': 'bfg9000'},
                               _symbols=self.symbols)
        self.assertIsInstance(builder, Bfg9000Builder)
        self.assertEqual(builder.name, 'foo')

    def test_make_string(self):
        builder = make_builder(self.pkg, 'bfg9000', _symbols=self.symbols)
        self.assertIsInstance(builder, Bfg9000Builder)
        self.assertEqual(builder.name, 'foo')

    def test_unknown_builder(self):
        with self.assertRaises(FieldError):
            make_builder(self.pkg, {'type': 'goofy'}, _symbols=self.symbols)

    def test_no_builder(self):
        with self.assertRaises(TypeError):
            make_builder(self.pkg, None, _symbols=self.symbols)

    def test_invalid_keys(self):
        with self.assertRaises(TypeError):
            make_builder(self.pkg, {'type': 'bfg9000', 'unknown': 'blah'},
                         _symbols=self.symbols)

    def test_invalid_values(self):
        with self.assertRaises(FieldError):
            make_builder(self.pkg, {'type': 'bfg9000', 'extra_args': 1},
                         _symbols=self.symbols)
