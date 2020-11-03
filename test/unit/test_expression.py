from unittest import TestCase
from yaml.error import Mark

from mopack.expression import *


class TestEvaluate(TestCase):
    symbols = {
        'foo': "foo",
    }

    def test_bool_literal(self):
        self.assertEqual(evaluate(self.symbols, 'true'), True)
        self.assertEqual(evaluate(self.symbols, 'false'), False)

    def test_equal(self):
        self.assertEqual(evaluate(self.symbols, '"foo" == "foo"'), True)
        self.assertEqual(evaluate(self.symbols, '"foo" == "bar"'), False)
        self.assertEqual(evaluate(self.symbols, 'foo == "foo"'), True)
        self.assertEqual(evaluate(self.symbols, 'foo == "bar"'), False)

    def test_not_equal(self):
        self.assertEqual(evaluate(self.symbols, '"foo" != "foo"'), False)
        self.assertEqual(evaluate(self.symbols, '"foo" != "bar"'), True)
        self.assertEqual(evaluate(self.symbols, 'foo != "foo"'), False)
        self.assertEqual(evaluate(self.symbols, 'foo != "bar"'), True)

    def test_and(self):
        self.assertEqual(evaluate(self.symbols, 'foo == "foo" && true'), True)
        self.assertEqual(evaluate(self.symbols, 'foo == "foo" && false'),
                         False)
        self.assertEqual(evaluate(self.symbols, 'foo == "bar" && true'), False)
        self.assertEqual(evaluate(self.symbols, 'foo == "bar" && false'),
                         False)

    def test_or(self):
        self.assertEqual(evaluate(self.symbols, 'foo == "foo" || true'), True)
        self.assertEqual(evaluate(self.symbols, 'foo == "foo" || false'), True)
        self.assertEqual(evaluate(self.symbols, 'foo == "bar" || true'), True)
        self.assertEqual(evaluate(self.symbols, 'foo == "bar" || false'),
                         False)

    def test_not(self):
        self.assertEqual(evaluate(self.symbols, '!("foo" == "foo")'), False)
        self.assertEqual(evaluate(self.symbols, '!("foo" == "bar")'), True)
        self.assertEqual(evaluate(self.symbols, '!(foo == "foo")'), False)
        self.assertEqual(evaluate(self.symbols, '!(foo == "bar")'), True)

    def test_invalid(self):
        with self.assertRaises(ParseException):
            evaluate(self.symbols, 'foo ==')


class TestToYamlError(TestCase):
    def test_convert(self):
        try:
            evaluate({}, '"foo" ==')
        except ParseException as e:
            err = to_yaml_error(e, None, Mark('name', 10, 1, 2, None, None))
        self.assertEqual(err.context, 'while parsing expression')
        self.assertEqual(err.context_mark, None)
        self.assertEqual(err.problem, "Expected end of text, found '='")
        self.assertEqual(err.problem_mark.name, 'name')
        self.assertEqual(err.problem_mark.index, 16)
        self.assertEqual(err.problem_mark.line, 1)
        self.assertEqual(err.problem_mark.column, 8)
