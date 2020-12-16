from unittest import TestCase

from mopack.placeholder import *


class TestPlaceholder(TestCase):
    def test_construct_empty(self):
        s = PlaceholderString()
        self.assertEqual(s.bits, ())
        self.assertEqual(s.unboxed_bits, ())

    def test_construct_single_str(self):
        s = PlaceholderString('foo')
        self.assertEqual(s.bits, ('foo',))
        self.assertEqual(s.unboxed_bits, ('foo',))

    def test_construct_coalesce_str(self):
        s = PlaceholderString('foo', 'bar', 'baz')
        self.assertEqual(s.bits, ('foobarbaz',))
        self.assertEqual(s.unboxed_bits, ('foobarbaz',))

    def test_construct_single_placeholder(self):
        p = PlaceholderValue(1)
        s = PlaceholderString(p)
        self.assertEqual(s.bits, (p,))
        self.assertEqual(s.unboxed_bits, (1,))

    def test_construct_multiple_placeholders(self):
        p1 = PlaceholderValue(1)
        p2 = PlaceholderValue(2)
        s = PlaceholderString(p1, p2)
        self.assertEqual(s.bits, (p1, p2))
        self.assertEqual(s.unboxed_bits, (1, 2))

    def test_construct_nested(self):
        s1 = PlaceholderString('foo')
        s2 = PlaceholderString('bar')
        s = PlaceholderString(s1, s2)
        self.assertEqual(s.bits, ('foobar',))
        self.assertEqual(s.unboxed_bits, ('foobar',))

    def test_construct_mixed(self):
        p1 = PlaceholderValue(1)
        p2 = PlaceholderValue(2)
        ps = PlaceholderString('foo', p1, 'bar')
        s = PlaceholderString('goat', ps, p2, 'panda')
        self.assertEqual(s.bits, ('goatfoo', p1, 'bar', p2, 'panda'))
        self.assertEqual(s.unboxed_bits, ('goatfoo', 1, 'bar', 2, 'panda'))

    def test_simplify(self):
        self.assertEqual(PlaceholderString().simplify(), '')
        self.assertEqual(PlaceholderString().simplify(False), '')
        self.assertEqual(PlaceholderString('foo').simplify(), 'foo')
        self.assertEqual(PlaceholderString('foo').simplify(False), 'foo')

        p = PlaceholderValue(1)
        self.assertEqual(PlaceholderString(p).simplify(), 1)
        self.assertIs(PlaceholderString(p).simplify(False), p)

        s = PlaceholderString('foo', p)
        self.assertIs(s.simplify(), s)
        self.assertIs(s.simplify(False), s)

    def test_make(self):
        p = PlaceholderValue(1)
        self.assertEqual(PlaceholderString.make(), '')
        self.assertEqual(PlaceholderString.make(simplify=False),
                         PlaceholderString())

        self.assertEqual(PlaceholderString.make('foo'), 'foo')
        self.assertEqual(PlaceholderString.make('foo', simplify=False),
                         PlaceholderString('foo'))

        self.assertEqual(PlaceholderString.make(p), 1)
        self.assertEqual(PlaceholderString.make(p, simplify=False),
                         PlaceholderString(p))

        self.assertEqual(PlaceholderString.make('foo', p),
                         PlaceholderString('foo', p))
        self.assertEqual(PlaceholderString.make('foo', p, simplify=False),
                         PlaceholderString('foo', p))

    def test_add(self):
        p = PlaceholderValue(1)
        s = PlaceholderString()
        self.assertEqual(s + 'foo', PlaceholderString('foo'))
        self.assertEqual('foo' + s, PlaceholderString('foo'))
        self.assertEqual(s + p, PlaceholderString(p))
        self.assertEqual(p + s, PlaceholderString(p))

        s = PlaceholderString('foo')
        self.assertEqual(s + 'bar', PlaceholderString('foobar'))
        self.assertEqual('bar' + s, PlaceholderString('barfoo'))
        self.assertEqual(s + p, PlaceholderString('foo', p))
        self.assertEqual(p + s, PlaceholderString(p, 'foo'))

    def test_stash_empty(self):
        s = PlaceholderString()
        stashed, placeholders = s.stash()
        self.assertEqual(stashed, '')
        self.assertEqual(placeholders, [])

        self.assertEqual(PlaceholderString.unstash(stashed, placeholders), '')
        self.assertEqual(PlaceholderString.unstash(
            stashed, placeholders, simplify=False
        ), s)

    def test_stash_str(self):
        s = PlaceholderString('foo')
        stashed, placeholders = s.stash()
        self.assertEqual(stashed, 'foo')
        self.assertEqual(placeholders, [])

        self.assertEqual(PlaceholderString.unstash(
            stashed, placeholders
        ), 'foo')
        self.assertEqual(PlaceholderString.unstash(
            stashed, placeholders, simplify=False
        ), s)

    def test_stash_str_escape(self):
        s = PlaceholderString('foo\x11bar')
        stashed, placeholders = s.stash()
        self.assertEqual(stashed, 'foo\x11\x13bar')
        self.assertEqual(placeholders, [])

        self.assertEqual(PlaceholderString.unstash(
            stashed, placeholders
        ), 'foo\x11bar')
        self.assertEqual(PlaceholderString.unstash(
            stashed, placeholders, simplify=False
        ), s)

    def test_stash_placeholder(self):
        p = PlaceholderValue(1)
        s = PlaceholderString(p)
        stashed, placeholders = s.stash()
        self.assertEqual(stashed, '\x110\x13')
        self.assertEqual(placeholders, [p])

        self.assertEqual(PlaceholderString.unstash(stashed, placeholders), 1)
        self.assertEqual(PlaceholderString.unstash(
            stashed, placeholders, simplify=False
        ), s)

    def test_stash_mixed(self):
        p = PlaceholderValue(1)
        s = PlaceholderString('foo', p, 'bar\x11baz')
        stashed, placeholders = s.stash()
        self.assertEqual(stashed, 'foo\x110\x13bar\x11\x13baz')
        self.assertEqual(placeholders, [p])

        self.assertEqual(PlaceholderString.unstash(stashed, placeholders), s)
        self.assertEqual(PlaceholderString.unstash(
            stashed, placeholders, simplify=False
        ), s)

    def test_placeholder(self):
        self.assertEqual(placeholder(1),
                         PlaceholderString(PlaceholderValue(1)))
