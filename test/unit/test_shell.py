import os
from unittest import TestCase

from mopack.path import Path
from mopack.placeholder import placeholder
from mopack.shell import *

srcdir = Path('srcdir', '')
srcdir_ph = placeholder(srcdir)


class TestQuotePosix(TestCase):
    def assertQuote(self, original, quoted, force_quoted=None):
        if force_quoted is None:
            force_quoted = quoted
        self.assertEqual(quote_posix(original), quoted)
        self.assertEqual(quote_posix(original, force=True), force_quoted)

    def test_empty(self):
        self.assertQuote('', "''")

    def test_simple(self):
        self.assertQuote('foo', 'foo', "'foo'")

    def test_space(self):
        self.assertQuote('foo bar', "'foo bar'")

    def test_quote(self):
        self.assertQuote('"foo"', "'\"foo\"'")
        self.assertQuote("'foo'", r"\''foo'\'")
        self.assertQuote("'foo'z", r"\''foo'\''z'")
        self.assertQuote("a'foo'", r"'a'\''foo'\'")
        self.assertQuote("a'foo'z", r"'a'\''foo'\''z'")

    def test_escaped_quote(self):
        self.assertQuote(r"\'foobar", r"'\'\''foobar'")
        self.assertQuote(r"foo\'bar", r"'foo\'\''bar'")
        self.assertQuote(r"foobar\'", r"'foobar\'\'")

    def test_shell_chars(self):
        self.assertQuote('&&', "'&&'")
        self.assertQuote('>', "'>'")
        self.assertQuote('|', "'|'")

    def test_invalid(self):
        with self.assertRaises(TypeError):
            quote_posix(1)


class TestQuoteWindows(TestCase):
    def assertQuote(self, original, quoted, force_quoted=None,
                    escape_quoted=None):
        if force_quoted is None:
            force_quoted = quoted
        if escape_quoted is None:
            escape_quoted = quoted
        self.assertEqual(quote_windows(original), quoted)
        self.assertEqual(quote_windows(original, force=True), force_quoted)
        self.assertEqual(quote_windows(original, escape_percent=True),
                         escape_quoted)

    def test_empty(self):
        self.assertQuote('', '""')

    def test_simple(self):
        self.assertQuote('foo', 'foo', '"foo"')

    def test_space(self):
        self.assertQuote('foo bar', '"foo bar"')

    def test_quote(self):
        self.assertQuote('"foo"', r'"\"foo\""')
        self.assertQuote('"foo"z', r'"\"foo\"z"')
        self.assertQuote('a"foo"', r'"a\"foo\""')
        self.assertQuote('a"foo"z', r'"a\"foo\"z"')

    def test_escaped_quote(self):
        self.assertQuote(r'\"foobar', r'"\\\"foobar"')
        self.assertQuote(r'foo\"bar', r'"foo\\\"bar"')
        self.assertQuote(r'foobar\"', r'"foobar\\\""')

    def test_backslash(self):
        self.assertQuote(r'foo\bar', r'foo\bar', r'"foo\bar"')
        self.assertQuote('foo\\bar\\', r'"foo\bar\\"')

    def test_escape_percent(self):
        self.assertQuote('100%', r'100%', r'"100%"', r'100%%')
        self.assertQuote('"100%"', r'"\"100%\""', escape_quoted=r'"\"100%%\""')

    def test_shell_chars(self):
        self.assertQuote('&&', '"&&"')
        self.assertQuote('>', '">"')
        self.assertQuote('|', '"|"')

    def test_invalid(self):
        with self.assertRaises(TypeError):
            quote_windows(1)


class TestSplitPosix(TestCase):
    def assertSplitEqual(self, value, expected, **kwargs):
        self.assertEqual(split_posix_str(value, **kwargs), expected)
        self.assertEqual(split_posix(value, **kwargs),
                         ShellArguments(expected))

    def test_single(self):
        self.assertSplitEqual('foo', ['foo'])
        self.assertSplitEqual(' foo', ['foo'])
        self.assertSplitEqual('foo ', ['foo'])
        self.assertSplitEqual(' foo ', ['foo'])

    def test_multiple(self):
        self.assertSplitEqual('foo bar baz', ['foo', 'bar', 'baz'])

    def test_quote(self):
        self.assertSplitEqual('foo "bar baz"', ['foo', 'bar baz'])
        self.assertSplitEqual('foo"bar baz"', ['foobar baz'])

    def test_type(self):
        self.assertSplitEqual('foo bar baz', ('foo', 'bar', 'baz'), type=tuple)

    def test_escapes(self):
        self.assertSplitEqual('foo\\ bar', ['foo\\', 'bar'])
        self.assertSplitEqual('foo\\ bar', ['foo bar'], escapes=True)

    def test_placeholder(self):
        self.assertEqual(split_posix(srcdir_ph), ShellArguments([srcdir]))
        self.assertEqual(split_posix('gcc ' + srcdir_ph),
                         ShellArguments(['gcc', srcdir]))
        self.assertEqual(split_posix('--srcdir=' + srcdir_ph),
                         ShellArguments([('--srcdir=', srcdir)]))
        self.assertEqual(split_posix('"prefix ' + srcdir_ph + '"'),
                         ShellArguments([('prefix ', srcdir)]))
        self.assertEqual(split_posix("'prefix " + srcdir_ph + "'"),
                         ShellArguments([('prefix ', srcdir)]))

    def test_invalid(self):
        self.assertRaises(TypeError, split_posix_str, 1)
        self.assertRaises(TypeError, split_posix, 1)
        self.assertRaises(TypeError, split_posix_str, srcdir_ph)


class TestSplitWindows(TestCase):
    def assertSplitEqual(self, value, expected, **kwargs):
        self.assertEqual(split_windows_str(value, **kwargs), expected)
        self.assertEqual(split_windows(value, **kwargs),
                         ShellArguments(expected))

    def test_single(self):
        self.assertSplitEqual('foo', ['foo'])
        self.assertSplitEqual(' foo', ['foo'])
        self.assertSplitEqual('foo ', ['foo'])
        self.assertSplitEqual(' foo ', ['foo'])

    def test_multiple(self):
        self.assertSplitEqual('foo bar baz', ['foo', 'bar', 'baz'])

    def test_backslash(self):
        self.assertSplitEqual(r'C:\path\to\file', [r'C:\path\to\file'])

    def test_quote(self):
        self.assertSplitEqual('foo "bar baz"', ['foo', 'bar baz'])
        self.assertSplitEqual('foo"bar baz"', ['foobar baz'])
        self.assertSplitEqual(r'foo "c:\path\\"', ['foo', 'c:\\path\\'])
        self.assertSplitEqual('foo "it\'s \\"good\\""',
                              ['foo', 'it\'s "good"'])

    def test_type(self):
        self.assertSplitEqual('foo bar baz', ('foo', 'bar', 'baz'), type=tuple)

    def test_placeholder(self):
        self.assertEqual(split_windows(srcdir_ph), ShellArguments([srcdir]))
        self.assertEqual(split_windows('gcc ' + srcdir_ph),
                         ShellArguments(['gcc', srcdir]))
        self.assertEqual(split_windows('--srcdir=' + srcdir_ph),
                         ShellArguments([('--srcdir=', srcdir)]))
        self.assertEqual(split_windows('"prefix ' + srcdir_ph + '"'),
                         ShellArguments([('prefix ', srcdir)]))

    def test_invalid(self):
        self.assertRaises(TypeError, split_windows_str, 1)
        self.assertRaises(TypeError, split_windows, 1)
        self.assertRaises(TypeError, split_windows_str, srcdir_ph)


class TestShellArguments(TestCase):
    def test_subscript(self):
        s = ShellArguments(['foo', 'bar', 'baz'])
        self.assertEqual(s[1], 'bar')

        s[1] = 'goat'
        self.assertEqual(list(s), ['foo', 'goat', 'baz'])

        del s[1]
        self.assertEqual(list(s), ['foo', 'baz'])

    def test_len(self):
        s = ShellArguments()
        self.assertEqual(len(s), 0)

        s = ShellArguments(['foo', 'bar', 'baz'])
        self.assertEqual(len(s), 3)

    def test_iter(self):
        s = ShellArguments(['foo', 'bar', 'baz'])
        self.assertEqual(list(iter(s)), ['foo', 'bar', 'baz'])

    def test_mutate(self):
        s = ShellArguments()
        s.append('foo')
        self.assertEqual(list(s), ['foo'])

        s.extend(['bar', 'baz'])
        self.assertEqual(list(s), ['foo', 'bar', 'baz'])

        s.insert(0, 'goat')
        self.assertEqual(list(s), ['goat', 'foo', 'bar', 'baz'])

    def test_fill_empty(self):
        s = ShellArguments()
        self.assertEqual(s.fill(), [])

    def test_fill_string(self):
        s = ShellArguments(['foo'])
        self.assertEqual(s.fill(), ['foo'])

        s = ShellArguments(['foo', 'bar', 'baz'])
        self.assertEqual(s.fill(), ['foo', 'bar', 'baz'])

    def test_fill_path(self):
        s = ShellArguments([srcdir])
        self.assertEqual(s.fill(srcdir='${srcdir}'), ['${srcdir}'])
        self.assertEqual(s.fill(srcdir=os.path.abspath('/path/to/srcdir')),
                         [os.path.abspath('/path/to/srcdir')])

    def test_fill_path_str(self):
        s = ShellArguments([('--srcdir=', srcdir)])
        self.assertEqual(s.fill(srcdir='${srcdir}'), ['--srcdir=${srcdir}'])
        self.assertEqual(s.fill(srcdir=os.path.abspath('/path/to/srcdir')),
                         ['--srcdir=' + os.path.abspath('/path/to/srcdir')])

    def test_rehydrate(self):
        s = ShellArguments()
        data = s.dehydrate()
        self.assertEqual(ShellArguments.rehydrate(data), s)

        s = ShellArguments(['foo'])
        data = s.dehydrate()
        self.assertEqual(ShellArguments.rehydrate(data), s)

        s = ShellArguments([srcdir])
        data = s.dehydrate()
        self.assertEqual(ShellArguments.rehydrate(data), s)

        s = ShellArguments([('--srcdir=', srcdir)])
        data = s.dehydrate()
        self.assertEqual(ShellArguments.rehydrate(data), s)

        s = ShellArguments(['gcc', ('--srcdir=', srcdir), srcdir])
        data = s.dehydrate()
        self.assertEqual(ShellArguments.rehydrate(data), s)
