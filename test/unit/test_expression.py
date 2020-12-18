from unittest import TestCase
from yaml.error import Mark

from mopack.expression import *


class TestEvaluate(TestCase):
    symbols = {
        'foo': 'Foo',
        'bar': {'baz': 'Baz'}
    }

    def assertEvaluate(self, expr, result):
        braced = '${{ ' + expr + ' }}'
        self.assertEqual(evaluate(self.symbols, braced), result)
        self.assertEqual(evaluate(self.symbols, braced, True), result)
        self.assertEqual(evaluate(self.symbols, expr, True), result)

    def test_non_expression(self):
        self.assertEqual(evaluate(self.symbols, ''), '')
        self.assertEqual(evaluate(self.symbols, 'foo'), 'foo')

        self.assertEqual(evaluate(self.symbols, '$$'), '$')
        self.assertEqual(evaluate(self.symbols, '$$', True), '$')

        with self.assertRaises(ParseException):
            evaluate(self.symbols, '$!')
        with self.assertRaises(ParseException):
            evaluate(self.symbols, '$!', True)

    def test_index(self):
        self.assertEvaluate('bar["baz"]', 'Baz')
        self.assertEvaluate('(bar)["baz"]', 'Baz')
        self.assertEvaluate('(bar)["nonexist"]', None)

    def test_string_literal(self):
        self.assertEvaluate("'foo'", 'foo')
        self.assertEvaluate('"foo"', 'foo')
        self.assertEvaluate("'foo\\nbar'", 'foo\nbar')

        self.assertEvaluate("'${{ foo }}'", '${{ foo }}')
        self.assertEqual(evaluate(self.symbols, "${{ '${{ foo }}' }}"),
                         '${{ foo }}')
        self.assertEqual(evaluate(self.symbols, "${{ 'foo }}' }}"), 'foo }}')

    def test_bool_literal(self):
        self.assertEvaluate('true', True)
        self.assertEvaluate('false', False)

    def test_null_literal(self):
        self.assertEvaluate('null', None)

    def test_add(self):
        self.assertEvaluate('"Foo" + "Bar"', 'FooBar')
        self.assertEvaluate('foo + "Bar"', 'FooBar')
        self.assertEvaluate('"Foo" + bar["baz"]', 'FooBaz')
        self.assertEvaluate('foo + bar["baz"]', 'FooBaz')

    def test_equal(self):
        self.assertEvaluate('"Foo" == "Foo"', True)
        self.assertEvaluate('"Foo" == "Bar"', False)
        self.assertEvaluate('foo == "Foo"', True)
        self.assertEvaluate('foo == "Bar"', False)
        self.assertEvaluate('foo == bar', False)

    def test_not_equal(self):
        self.assertEvaluate('"Foo" != "Foo"', False)
        self.assertEvaluate('"Foo" != "Bar"', True)
        self.assertEvaluate('foo != "Foo"', False)
        self.assertEvaluate('foo != "Bar"', True)
        self.assertEvaluate('foo != bar', True)

    def test_and(self):
        self.assertEvaluate('foo == "Foo" && true', True)
        self.assertEvaluate('foo == "Foo" && false', False)
        self.assertEvaluate('foo == "Bar" && true', False)
        self.assertEvaluate('foo == "Bar" && false', False)

    def test_or(self):
        self.assertEvaluate('foo == "Foo" || true', True)
        self.assertEvaluate('foo == "Foo" || false', True)
        self.assertEvaluate('foo == "Bar" || true', True)
        self.assertEvaluate('foo == "Bar" || false', False)

    def test_not(self):
        self.assertEvaluate('!("Foo" == "Foo")', False)
        self.assertEvaluate('!("Foo" == "Bar")', True)
        self.assertEvaluate('!(foo == "Foo")', False)
        self.assertEvaluate('!(foo == "Bar")', True)

    def test_ternary(self):
        self.assertEvaluate('true ? "foo" : "bar"', 'foo')
        self.assertEvaluate('false ? "foo" : "bar"', 'bar')

    def test_mixed(self):
        self.assertEqual(evaluate(
            self.symbols, "1 ${{ 'foo' }} 2 ${{ 'bar' }} 3"
        ), '1 foo 2 bar 3')

    def test_simple_identifier(self):
        self.assertEqual(evaluate(self.symbols, '$foo'), 'Foo')
        self.assertEqual(evaluate(self.symbols, '$foo', True), 'Foo')

    def test_invalid_syntax(self):
        with self.assertRaises(ParseException):
            evaluate(self.symbols, '${{ foo == }}')
        with self.assertRaises(ParseException):
            evaluate(self.symbols, '${{ foo == }}', True)
        with self.assertRaises(ParseException):
            evaluate(self.symbols, 'foo ==', True)

    def test_undefined_symbol(self):
        with self.assertRaises(SemanticException):
            evaluate(self.symbols, '${{ bad == "bad" }}')
        with self.assertRaises(SemanticException):
            evaluate(self.symbols, '${{ bad == "bad" }}', True)
        with self.assertRaises(SemanticException):
            evaluate(self.symbols, 'bad == "bad"', True)


class TestToYamlError(TestCase):
    def test_convert_parse_exc(self):
        try:
            evaluate({}, '${{ "Foo" == }}')
        except ParseException as e:
            err = to_yaml_error(e, None, Mark('name', 10, 1, 2, None, None))
        self.assertEqual(err.context, 'while parsing expression')
        self.assertEqual(err.context_mark, None)
        self.assertEqual(err.problem, "Expected end of text, found '$'")
        self.assertEqual(err.problem_mark.name, 'name')
        self.assertEqual(err.problem_mark.index, 10)
        self.assertEqual(err.problem_mark.line, 1)
        self.assertEqual(err.problem_mark.column, 2)

    def test_convert_parse_exc_if(self):
        try:
            evaluate({}, '"Foo" ==', True)
        except ParseException as e:
            err = to_yaml_error(e, None, Mark('name', 10, 1, 2, None, None))
        self.assertEqual(err.context, 'while parsing expression')
        self.assertEqual(err.context_mark, None)
        self.assertEqual(err.problem, "Expected end of text, found '='")
        self.assertEqual(err.problem_mark.name, 'name')
        self.assertEqual(err.problem_mark.index, 16)
        self.assertEqual(err.problem_mark.line, 1)
        self.assertEqual(err.problem_mark.column, 8)

    def test_convert_semantic_exc(self):
        try:
            evaluate({}, '${{ foo == "Foo" }}')
        except SemanticException as e:
            err = to_yaml_error(e, None, Mark('name', 10, 1, 2, None, None))
        self.assertEqual(err.context, 'while parsing expression')
        self.assertEqual(err.context_mark, None)
        self.assertEqual(err.problem, "undefined symbol 'foo'")
        self.assertEqual(err.problem_mark.name, 'name')
        self.assertEqual(err.problem_mark.index, 14)
        self.assertEqual(err.problem_mark.line, 1)
        self.assertEqual(err.problem_mark.column, 6)

    def test_convert_semantic_exc_if(self):
        try:
            evaluate({}, 'foo == "Foo"', True)
        except SemanticException as e:
            err = to_yaml_error(e, None, Mark('name', 10, 1, 2, None, None))
        self.assertEqual(err.context, 'while parsing expression')
        self.assertEqual(err.context_mark, None)
        self.assertEqual(err.problem, "undefined symbol 'foo'")
        self.assertEqual(err.problem_mark.name, 'name')
        self.assertEqual(err.problem_mark.index, 10)
        self.assertEqual(err.problem_mark.line, 1)
        self.assertEqual(err.problem_mark.column, 2)
