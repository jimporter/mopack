from unittest import TestCase

from mopack.shell import *


class TestSplitWindows(TestCase):
    def test_single(self):
        self.assertEqual(split_windows('foo'), ['foo'])
        self.assertEqual(split_windows(' foo'), ['foo'])
        self.assertEqual(split_windows('foo '), ['foo'])
        self.assertEqual(split_windows(' foo '), ['foo'])

    def test_multiple(self):
        self.assertEqual(split_windows('foo bar baz'), ['foo', 'bar', 'baz'])

    def test_backslash(self):
        self.assertEqual(split_windows(r'C:\path\to\file'),
                         [r'C:\path\to\file'])

    def test_quote(self):
        self.assertEqual(split_windows('foo "bar baz"'), ['foo', 'bar baz'])
        self.assertEqual(split_windows('foo"bar baz"'), ['foobar baz'])
        self.assertEqual(split_windows(r'foo "c:\path\\"'),
                         ['foo', 'c:\\path\\'])
        self.assertEqual(split_windows('foo "it\'s \\"good\\""'),
                         ['foo', 'it\'s "good"'])

    def test_type(self):
        self.assertEqual(split_windows('foo bar baz', type=tuple),
                         ('foo', 'bar', 'baz'))

    def test_invalid(self):
        self.assertRaises(TypeError, split_windows, 1)


class TestSplitPosix(TestCase):
    def test_single(self):
        self.assertEqual(split_posix('foo'), ['foo'])

    def test_multiple(self):
        self.assertEqual(split_posix('foo bar baz'), ['foo', 'bar', 'baz'])

    def test_quote(self):
        self.assertEqual(split_posix('foo "bar baz"'), ['foo', 'bar baz'])
        self.assertEqual(split_posix('foo"bar baz"'), ['foobar baz'])

    def test_type(self):
        self.assertEqual(split_posix('foo bar baz', type=tuple),
                         ('foo', 'bar', 'baz'))

    def test_escapes(self):
        self.assertEqual(split_posix('foo\\ bar'), ['foo\\', 'bar'])
        self.assertEqual(split_posix('foo\\ bar', escapes=True), ['foo bar'])

    def test_invalid(self):
        self.assertRaises(TypeError, split_posix, 1)
