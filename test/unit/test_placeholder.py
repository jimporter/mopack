from unittest import TestCase

from mopack.placeholder import *


class TestPlaceholder(TestCase):
    def test_construct_empty(self):
        s = PlaceholderString()
        self.assertEqual(s.bits, ())

    def test_construct_single_str(self):
        s = PlaceholderString('foo')
        self.assertEqual(s.bits, ('foo',))

    def test_construct_coalesce_str(self):
        s = PlaceholderString('foo', 'bar', 'baz')
        self.assertEqual(s.bits, ('foobarbaz',))

    def test_construct_single_placeholder(self):
        p = PlaceholderValue(1)
        s = PlaceholderString(p)
        self.assertEqual(s.bits, (p,))

    def test_construct_multiple_placeholders(self):
        p1 = PlaceholderValue(1)
        p2 = PlaceholderValue(2)
        s = PlaceholderString(p1, p2)
        self.assertEqual(s.bits, (p1, p2))

    def test_construct_nested(self):
        s1 = PlaceholderString('foo')
        s2 = PlaceholderString('bar')
        s = PlaceholderString(s1, s2)
        self.assertEqual(s.bits, ('foobar',))

    def test_construct_mixed(self):
        p1 = PlaceholderValue(1)
        p2 = PlaceholderValue(2)
        ps = PlaceholderString('foo', p1, 'bar')
        s = PlaceholderString('goat', ps, p2, 'panda')
        self.assertEqual(s.bits, ('goatfoo', p1, 'bar', p2, 'panda'))

    def test_make(self):
        p = PlaceholderValue(1)

        self.assertEqual(PlaceholderString.make(), PlaceholderString())
        self.assertEqual(PlaceholderString.make(simplify=True), '')

        self.assertEqual(PlaceholderString.make('foo'),
                         PlaceholderString('foo'))
        self.assertEqual(PlaceholderString.make('foo', simplify=True), 'foo')

        self.assertEqual(PlaceholderString.make(p), PlaceholderString(p))
        self.assertEqual(PlaceholderString.make(p, simplify=True),
                         PlaceholderString(p))

        self.assertEqual(PlaceholderString.make('foo', p),
                         PlaceholderString('foo', p))
        self.assertEqual(PlaceholderString.make('foo', p, simplify=True),
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

    def test_unbox(self):
        p = PlaceholderValue(1)

        s = PlaceholderString()
        self.assertEqual(s.unbox(), ())
        self.assertEqual(s.unbox(simplify=True), '')

        s = PlaceholderString('foo')
        self.assertEqual(s.unbox(), ('foo',))
        self.assertEqual(s.unbox(simplify=True), 'foo')

        s = PlaceholderString(p)
        self.assertEqual(s.unbox(), (1,))
        self.assertEqual(s.unbox(simplify=True), 1)

        s = PlaceholderString('foo', p, 'bar')
        self.assertEqual(s.unbox(), ('foo', 1, 'bar'))
        self.assertEqual(s.unbox(simplify=True), ('foo', 1, 'bar'))

    def test_replace(self):
        p1 = PlaceholderValue(1)
        p2 = PlaceholderValue(2)

        s = PlaceholderString()
        self.assertEqual(s.replace(1, 'A'), s)
        self.assertEqual(s.replace(1, 'A',  simplify=True), '')

        s = PlaceholderString('foo')
        self.assertEqual(s.replace(1, 'A'), s)
        self.assertEqual(s.replace(1, 'A', simplify=True), 'foo')

        s = PlaceholderString(p1)
        self.assertEqual(s.replace(1, 'A'), PlaceholderString('A'))
        self.assertEqual(s.replace(1, 'A', simplify=True), 'A')

        s = PlaceholderString(p2)
        self.assertEqual(s.replace(1, 'A'), s)
        self.assertEqual(s.replace(1, 'A', simplify=True), s)

        s = PlaceholderString('foo', p1, 'bar')
        self.assertEqual(s.replace(1, 'A'), PlaceholderString('fooAbar'))
        self.assertEqual(s.replace(1, 'A', simplify=True), 'fooAbar')

        s = PlaceholderString('foo', p1, 'bar', p2)
        self.assertEqual(s.replace(1, 'A'), PlaceholderString('fooAbar', p2))
        self.assertEqual(s.replace(1, 'A', simplify=True),
                         PlaceholderString('fooAbar', p2))

    def test_stash_empty(self):
        s = PlaceholderString()
        stashed, placeholders = s.stash()
        self.assertEqual(stashed, '')
        self.assertEqual(placeholders, [])

        self.assertEqual(PlaceholderString.unstash(stashed, placeholders), s)

    def test_stash_str(self):
        s = PlaceholderString('foo')
        stashed, placeholders = s.stash()
        self.assertEqual(stashed, 'foo')
        self.assertEqual(placeholders, [])

        self.assertEqual(PlaceholderString.unstash(stashed, placeholders), s)

    def test_stash_str_escape(self):
        s = PlaceholderString('foo\x11bar')
        stashed, placeholders = s.stash()
        self.assertEqual(stashed, 'foo\x11\x13bar')
        self.assertEqual(placeholders, [])

        self.assertEqual(PlaceholderString.unstash(stashed, placeholders), s)

    def test_stash_placeholder(self):
        p = PlaceholderValue(1)
        s = PlaceholderString(p)
        stashed, placeholders = s.stash()
        self.assertEqual(stashed, '\x110\x13')
        self.assertEqual(placeholders, [p])

        self.assertEqual(PlaceholderString.unstash(stashed, placeholders), s)

    def test_stash_mixed(self):
        p = PlaceholderValue(1)
        s = PlaceholderString('foo', p, 'bar\x11baz')
        stashed, placeholders = s.stash()
        self.assertEqual(stashed, 'foo\x110\x13bar\x11\x13baz')
        self.assertEqual(placeholders, [p])

        self.assertEqual(PlaceholderString.unstash(stashed, placeholders), s)

    def test_placeholder(self):
        self.assertEqual(placeholder(1),
                         PlaceholderString(PlaceholderValue(1)))


class TestMapRecursive(TestCase):
    @staticmethod
    def fn(value):
        return value.replace(1, 'A', simplify=True)

    def test_simple(self):
        self.assertEqual(map_recursive(None, self.fn), None)
        self.assertEqual(map_recursive(True, self.fn), True)
        self.assertEqual(map_recursive(1, self.fn), 1)
        self.assertEqual(map_recursive('foo', self.fn), 'foo')

    def test_placeholder(self):
        p = PlaceholderValue(1)
        PS = PlaceholderString

        self.assertEqual(map_recursive(PS(), self.fn), '')
        self.assertEqual(map_recursive(PS('foo'), self.fn), 'foo')
        self.assertEqual(map_recursive(PS('foo', p), self.fn), 'fooA')

    def test_list(self):
        s = PlaceholderString('foo', PlaceholderValue(1), 'bar')
        self.assertEqual(map_recursive([], self.fn), [])
        self.assertEqual(map_recursive(['foo'], self.fn), ['foo'])
        self.assertEqual(map_recursive([s], self.fn), ['fooAbar'])
        self.assertEqual(map_recursive(['foo', s], self.fn),
                         ['foo', 'fooAbar'])

    def test_dict(self):
        s = PlaceholderString('foo', PlaceholderValue(1), 'bar')
        self.assertEqual(map_recursive({}, self.fn), {})
        self.assertEqual(map_recursive({'key': 'foo'}, self.fn),
                         {'key': 'foo'})
        self.assertEqual(map_recursive({'key': s}, self.fn),
                         {'key': 'fooAbar'})
        self.assertEqual(map_recursive({'key1': 'foo', 'key2': s}, self.fn),
                         {'key1': 'foo', 'key2': 'fooAbar'})

    def test_mixed(self):
        s = PlaceholderString('foo', PlaceholderValue(1), 'bar')
        self.assertEqual(map_recursive({'key': ['<', s, '>']}, self.fn),
                         {'key': ['<', 'fooAbar', '>']})


class TestPlaceholderFD(TestCase):
    p1 = PlaceholderValue('FOO')
    p2 = PlaceholderValue('BAR')

    def setUp(self):
        self.fd = PlaceholderFD(self.p1.value, self.p2.value)

    def assertDehydrate(self, value, expected):
        dehydrated = self.fd.dehydrate(value)
        self.assertEqual(dehydrated, expected)
        self.assertEqual(self.fd.rehydrate(dehydrated), value)

    def test_dehydrate_simple(self):
        self.assertDehydrate(None, None)
        self.assertDehydrate(True, True)
        self.assertDehydrate(1, 1)
        self.assertDehydrate('foo', 'foo')

    def test_dehydrate_placeholder(self):
        PS = PlaceholderString

        self.assertDehydrate(PS(), {'_phs': []})
        self.assertDehydrate(PS('foo'), {'_phs': ['foo']})
        self.assertDehydrate(PS('foo', self.p1), {'_phs': ['foo', 0]})
        self.assertDehydrate(PS(self.p1, 'foo', self.p2, 'bar', self.p1),
                             {'_phs': [0, 'foo', 1, 'bar', 0]})

    def test_dehydrate_mixed(self):
        s = PlaceholderString('foo', self.p1, 'bar')
        self.assertDehydrate({'key': ['<', s, '>']},
                             {'key': ['<', {'_phs': ['foo', 0, 'bar']}, '>']})

    def test_dehydrate_unrecognized_placeholder(self):
        with self.assertRaises(ValueError):
            self.fd.dehydrate(PlaceholderString(PlaceholderValue('unknown')))
