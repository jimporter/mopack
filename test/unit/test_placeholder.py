from unittest import TestCase, mock

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

    def test_simplify(self):
        p = PlaceholderValue(1)

        s = PlaceholderString()
        self.assertEqual(s.simplify(), '')
        self.assertEqual(s.simplify(unbox=True), '')

        s = PlaceholderString('foo')
        self.assertEqual(s.simplify(), 'foo')
        self.assertEqual(s.simplify(unbox=True), 'foo')

        s = PlaceholderString(p)
        self.assertEqual(s.simplify(), s)
        self.assertEqual(s.simplify(unbox=True), 1)

        s = PlaceholderString('foo', p, 'bar')
        self.assertEqual(s.simplify(), s)
        self.assertEqual(s.simplify(unbox=True), s)

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

    def test_rehydrate(self):
        class IntRehydrator:
            @staticmethod
            def rehydrate(config, **kwargs):
                return int(config)

        with mock.patch('mopack.placeholder._known_placeholders',
                        [IntRehydrator]):
            ph = placeholder

            s = PlaceholderString()
            data = s.dehydrate()
            self.assertEqual(data, [])
            self.assertEqual(PlaceholderString.rehydrate(data), s)

            s = PlaceholderString('foo')
            data = s.dehydrate()
            self.assertEqual(data, ['foo'])
            self.assertEqual(PlaceholderString.rehydrate(data), s)

            s = PlaceholderString(ph(1))
            data = s.dehydrate()
            self.assertEqual(data, [1])
            self.assertEqual(PlaceholderString.rehydrate(data), s)

            s = PlaceholderString('foo=' + ph(1))
            data = s.dehydrate()
            self.assertEqual(data, ['foo=', 1])
            self.assertEqual(PlaceholderString.rehydrate(data), s)

            s = PlaceholderString('foo', 'bar=' + ph(1), 'baz')
            data = s.dehydrate()
            self.assertEqual(data, ['foobar=', 1, 'baz'])
            self.assertEqual(PlaceholderString.rehydrate(data), s)

    def test_placeholder(self):
        self.assertEqual(placeholder(1),
                         PlaceholderString(PlaceholderValue(1)))


class TestMapPlaceholder(TestCase):
    @staticmethod
    def fn(value):
        return value.replace(1, 'A', simplify=True)

    def test_simple(self):
        self.assertEqual(map_placeholder(None, self.fn), None)
        self.assertEqual(map_placeholder(True, self.fn), True)
        self.assertEqual(map_placeholder(1, self.fn), 1)
        self.assertEqual(map_placeholder('foo', self.fn), 'foo')

    def test_placeholder(self):
        p = PlaceholderValue(1)
        PS = PlaceholderString

        self.assertEqual(map_placeholder(PS(), self.fn), '')
        self.assertEqual(map_placeholder(PS('foo'), self.fn), 'foo')
        self.assertEqual(map_placeholder(PS('foo', p), self.fn), 'fooA')

    def test_list(self):
        s = PlaceholderString('foo', PlaceholderValue(1), 'bar')
        self.assertEqual(map_placeholder([], self.fn), [])
        self.assertEqual(map_placeholder(['foo'], self.fn), ['foo'])
        self.assertEqual(map_placeholder([s], self.fn), ['fooAbar'])
        self.assertEqual(map_placeholder(['foo', s], self.fn),
                         ['foo', 'fooAbar'])

    def test_dict(self):
        s = PlaceholderString('foo', PlaceholderValue(1), 'bar')
        self.assertEqual(map_placeholder({}, self.fn), {})
        self.assertEqual(map_placeholder({'key': 'foo'}, self.fn),
                         {'key': 'foo'})
        self.assertEqual(map_placeholder({'key': s}, self.fn),
                         {'key': 'fooAbar'})
        self.assertEqual(map_placeholder({'key1': 'foo', 'key2': s}, self.fn),
                         {'key1': 'foo', 'key2': 'fooAbar'})

    def test_mixed(self):
        s = PlaceholderString('foo', PlaceholderValue(1), 'bar')
        self.assertEqual(map_placeholder({'key': ['<', s, '>']}, self.fn),
                         {'key': ['<', 'fooAbar', '>']})
