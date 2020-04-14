from unittest import TestCase

from mopack import shell


class TestSplit(TestCase):
    def test_single(self):
        self.assertEqual(shell.split('foo'), ['foo'])

    def test_multiple(self):
        self.assertEqual(shell.split('foo bar baz'), ['foo', 'bar', 'baz'])

    def test_quote(self):
        self.assertEqual(shell.split('foo "bar baz"'), ['foo', 'bar baz'])
        self.assertEqual(shell.split('foo"bar baz"'), ['foobar baz'])

    def test_type(self):
        self.assertEqual(shell.split('foo bar baz', type=tuple),
                         ('foo', 'bar', 'baz'))

    def test_escapes(self):
        self.assertEqual(shell.split('foo\\ bar'), ['foo\\', 'bar'])
        self.assertEqual(shell.split('foo\\ bar', escapes=True), ['foo bar'])

    def test_invalid(self):
        self.assertRaises(TypeError, shell.split, 1)
