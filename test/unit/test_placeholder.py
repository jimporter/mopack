from unittest import TestCase, mock

from mopack.placeholder import *


class TestPlaceholder(TestCase):
    def test_construct_empty(self):
        with self.assertRaises(TypeError):
            PlaceholderString()

    def test_construct_str(self):
        with self.assertRaises(TypeError):
            PlaceholderString('foo')

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
        p = PlaceholderValue(1)
        s1 = PlaceholderString(p, 'foo')
        s2 = PlaceholderString('bar', p)
        s = PlaceholderString(s1, s2)
        self.assertEqual(s.bits, (p, 'foobar', p))

    def test_construct_coalesce_str(self):
        p = PlaceholderValue(1)
        s = PlaceholderString(p, 'foo', 'bar', 'baz')
        self.assertEqual(s.bits, (p, 'foobarbaz'))

    def test_construct_mixed(self):
        p1 = PlaceholderValue(1)
        p2 = PlaceholderValue(2)
        ps = PlaceholderString('foo', p1, 'bar')
        s = PlaceholderString('goat', ps, p2, 'panda')
        self.assertEqual(s.bits, ('goatfoo', p1, 'bar', p2, 'panda'))

    def test_make(self):
        p = PlaceholderValue(1)

        self.assertEqual(PlaceholderString.make(), '')
        self.assertEqual(PlaceholderString.make('foo'), 'foo')
        self.assertEqual(PlaceholderString.make(p), PlaceholderString(p))
        self.assertEqual(PlaceholderString.make('foo', p),
                         PlaceholderString('foo', p))

    def test_add(self):
        p1 = PlaceholderValue(1)
        p2 = PlaceholderValue(2)

        s = PlaceholderString(p1)
        self.assertEqual(s + 'foo', PlaceholderString(p1, 'foo'))
        self.assertEqual('foo' + s, PlaceholderString('foo', p1))
        self.assertEqual(s + p2, PlaceholderString(p1, p2))
        self.assertEqual(p2 + s, PlaceholderString(p2, p1))

        s = PlaceholderString('foo', p1, 'bar')
        self.assertEqual(s + 'baz', PlaceholderString('foo', p1, 'barbaz'))
        self.assertEqual('baz' + s, PlaceholderString('bazfoo', p1, 'bar'))
        self.assertEqual(s + p2, PlaceholderString('foo', p1, 'bar', p2))
        self.assertEqual(p2 + s, PlaceholderString(p2, 'foo', p1, 'bar'))

    def test_unbox(self):
        p = PlaceholderValue(1)

        s = PlaceholderString(p)
        self.assertEqual(s.unbox(), (1,))

        s = PlaceholderString('foo', p, 'bar')
        self.assertEqual(s.unbox(), ('foo', 1, 'bar'))

    def test_replace(self):
        p1 = PlaceholderValue(1)
        p2 = PlaceholderValue(2)

        s = PlaceholderString(p1)
        self.assertEqual(s.replace(1, 'A'), 'A')

        s = PlaceholderString(p2)
        self.assertEqual(s.replace(1, 'A'), s)

        s = PlaceholderString('foo', p1, 'bar')
        self.assertEqual(s.replace(1, 'A'), 'fooAbar')

        s = PlaceholderString('foo', p1, 'bar', p2)
        self.assertEqual(s.replace(1, 'A'), PlaceholderString('fooAbar', p2))

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

        with self.assertRaises(TypeError):
            placeholder('foo')


class TestMapPlaceholder(TestCase):
    @staticmethod
    def fn(value):
        return value.replace(1, 'A')

    def test_simple(self):
        self.assertEqual(map_placeholder(None, self.fn), None)
        self.assertEqual(map_placeholder(True, self.fn), True)
        self.assertEqual(map_placeholder(1, self.fn), 1)
        self.assertEqual(map_placeholder('foo', self.fn), 'foo')

    def test_placeholder(self):
        p = PlaceholderValue(1)

        s = PlaceholderString(p)
        self.assertEqual(map_placeholder(s, self.fn), 'A')

        s = PlaceholderString('foo', p)
        self.assertEqual(map_placeholder(s, self.fn), 'fooA')

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
