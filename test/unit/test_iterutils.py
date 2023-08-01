from collections import namedtuple
from unittest import TestCase

from mopack import iterutils
from mopack.yaml_tools import MarkedDict, MarkedList


class TestIsIterable(TestCase):
    def test_list(self):
        self.assertTrue(iterutils.isiterable([]))

    def test_marked_list(self):
        self.assertTrue(iterutils.isiterable(MarkedList()))

    def test_dict(self):
        self.assertFalse(iterutils.isiterable({}))

    def test_marked_dict(self):
        self.assertFalse(iterutils.isiterable(MarkedDict()))

    def test_generator(self):
        gen = (i for i in range(10))
        self.assertTrue(iterutils.isiterable(gen))

    def test_string(self):
        self.assertFalse(iterutils.isiterable('foo'))

    def test_none(self):
        self.assertFalse(iterutils.isiterable(None))


class TestIsSequence(TestCase):
    def test_list(self):
        self.assertTrue(iterutils.issequence([]))

    def test_marked_list(self):
        self.assertTrue(iterutils.issequence(MarkedList()))

    def test_dict(self):
        self.assertFalse(iterutils.issequence({}))

    def test_marked_dict(self):
        self.assertFalse(iterutils.issequence(MarkedDict()))

    def test_string(self):
        self.assertFalse(iterutils.issequence('foo'))

    def test_none(self):
        self.assertFalse(iterutils.issequence(None))


class TestIsMapping(TestCase):
    def test_list(self):
        self.assertFalse(iterutils.ismapping([]))

    def test_marked_list(self):
        self.assertFalse(iterutils.ismapping(MarkedList()))

    def test_dict(self):
        self.assertTrue(iterutils.ismapping({}))

    def test_marked_dict(self):
        self.assertTrue(iterutils.ismapping(MarkedDict()))

    def test_string(self):
        self.assertFalse(iterutils.ismapping('foo'))

    def test_none(self):
        self.assertFalse(iterutils.ismapping(None))


class TestIterate(TestCase):
    def test_none(self):
        self.assertEqual(list(iterutils.iterate(None)), [])

    def test_one(self):
        self.assertEqual(list(iterutils.iterate('foo')), ['foo'])

    def test_many(self):
        self.assertEqual(list(iterutils.iterate(['foo', 'bar'])),
                         ['foo', 'bar'])


class TestIteritems(TestCase):
    def test_list(self):
        self.assertEqual(
            list(iterutils.iteritems(['foo', 'bar'])),
            [(0, 'foo'), (1, 'bar')]
        )

    def test_dict(self):
        self.assertEqual(
            list(iterutils.iteritems({'foo': 'Foo', 'bar': 'Bar'})),
            [('foo', 'Foo'), ('bar', 'Bar')]
        )


class TestListify(TestCase):
    def test_none(self):
        self.assertEqual(iterutils.listify(None), [])

    def test_one(self):
        self.assertEqual(iterutils.listify('foo'), ['foo'])

    def test_many(self):
        x = ['foo', 'bar']
        res = iterutils.listify(x)
        self.assertEqual(res, x)
        self.assertTrue(x is res)

    def test_always_copy(self):
        x = ['foo', 'bar']
        res = iterutils.listify(x, always_copy=True)
        self.assertEqual(res, x)
        self.assertTrue(x is not res)

    def test_no_scalar(self):
        self.assertEqual(iterutils.listify(['foo'], scalar_ok=False), ['foo'])
        self.assertEqual(iterutils.listify(['foo'], always_copy=True,
                                           scalar_ok=False), ['foo'])
        self.assertRaises(TypeError, iterutils.listify, 1, scalar_ok=False)
        self.assertRaises(TypeError, iterutils.listify, 'foo', scalar_ok=False)

    def test_type(self):
        x = 'foo'
        res = iterutils.listify(x, type=tuple)
        self.assertEqual(res, ('foo',))

        y = ['foo', 'bar']
        res = iterutils.listify(y, type=tuple)
        self.assertEqual(res, ('foo', 'bar'))


class TestEachAttr(TestCase):
    def test_empty(self):
        self.assertEqual(list(iterutils.each_attr([], 'attr')), [])

    def test_has_attrs(self):
        T = namedtuple('T', ['attr'])
        self.assertEqual(list(iterutils.each_attr(
            [T('foo'), T('bar')], 'attr'
        )), ['foo', 'bar'])

    def test_no_attrs(self):
        self.assertEqual(list(iterutils.each_attr(['foo', 'bar'], 'attr')), [])

    def test_mixed(self):
        T = namedtuple('T', ['attr'])
        self.assertEqual(list(iterutils.each_attr(
            [T('foo'), 'bar'], 'attr'
        )), ['foo'])


class TestFlatten(TestCase):
    def test_empty(self):
        self.assertEqual(iterutils.flatten([]), [])
        self.assertEqual(iterutils.flatten(i for i in range(0)), [])

    def test_default_type(self):
        self.assertEqual(iterutils.flatten([[0, 1]] * 3), [0, 1, 0, 1, 0, 1])
        self.assertEqual(iterutils.flatten([i, i + 1] for i in range(3)),
                         [0, 1, 1, 2, 2, 3])

    def test_custom_type(self):
        class custom_list(list):
            def __eq__(self, rhs):
                return type(self) is type(rhs) and super().__eq__(rhs)

        self.assertEqual(iterutils.flatten([[0, 1]] * 3, custom_list),
                         custom_list([0, 1, 0, 1, 0, 1]))
        self.assertEqual(iterutils.flatten(([i, i + 1] for i in range(3)),
                                           custom_list),
                         custom_list([0, 1, 1, 2, 2, 3]))


class TestUniques(TestCase):
    def test_none(self):
        self.assertEqual(iterutils.uniques([]), [])

    def test_one(self):
        self.assertEqual(iterutils.uniques([1]), [1])

    def test_many(self):
        self.assertEqual(iterutils.uniques([1, 2, 1, 3]), [1, 2, 3])


class TestListView(TestCase):
    data = [1, 2, 3, 4]

    def test_len(self):
        self.assertEqual(len( iterutils.list_view(self.data) ), 4)
        self.assertEqual(len( iterutils.list_view(self.data, 2) ), 2)
        self.assertEqual(len( iterutils.list_view(self.data, 2, 3) ), 1)

    def test_index(self):
        view = iterutils.list_view(self.data)
        self.assertEqual(view[2], 3)
        self.assertRaises(IndexError, view.__getitem__, -1)
        self.assertRaises(IndexError, view.__getitem__, 4)

        view = iterutils.list_view(self.data, 2)
        self.assertEqual(view[1], 4)
        self.assertRaises(IndexError, view.__getitem__, -1)
        self.assertRaises(IndexError, view.__getitem__, 2)

        view = iterutils.list_view(self.data, 2, 3)
        self.assertEqual(view[0], 3)
        self.assertRaises(IndexError, view.__getitem__, -1)
        self.assertRaises(IndexError, view.__getitem__, 1)

    def test_slice(self):
        view = iterutils.list_view(self.data)
        viewslice = view[1:3]
        self.assertEqual(list(iter(viewslice)), [2, 3])
        self.assertRaises(ValueError, view.__getitem__, slice(None, None, 2))

        view = iterutils.list_view(self.data, 1)
        viewslice = view[1:3]
        self.assertEqual(list(iter(viewslice)), [3, 4])

    def test_iter(self):
        view = iterutils.list_view(self.data)
        self.assertEqual(list(iter(view)), self.data)

        view = iterutils.list_view(self.data, 2)
        self.assertEqual(list(iter(view)), [3, 4])

        view = iterutils.list_view(self.data, 2, 3)
        self.assertEqual(list(iter(view)), [3])

    def test_split_at(self):
        view = iterutils.list_view(self.data)
        a, b = view.split_at(2)
        self.assertEqual(list(a), [1, 2])
        self.assertEqual(list(b), [3, 4])

        a, b = view.split_at(-1)
        self.assertEqual(list(a), [])
        self.assertEqual(list(b), [1, 2, 3, 4])

        a, b = view.split_at(10)
        self.assertEqual(list(a), [1, 2, 3, 4])
        self.assertEqual(list(b), [])


class TestMergeIntoDict(TestCase):
    def test_merge_empty(self):
        d = {}
        iterutils.merge_into_dict(d, {})
        self.assertEqual(d, {})

        d = {}
        iterutils.merge_into_dict(d, {'foo': 1})
        self.assertEqual(d, {'foo': 1})

        d = {'foo': 1}
        iterutils.merge_into_dict(d, {})
        self.assertEqual(d, {'foo': 1})

    def test_merge(self):
        d = {'foo': 1}
        iterutils.merge_into_dict(d, {'bar': 2})
        self.assertEqual(d, {'foo': 1, 'bar': 2})

        d = {'foo': 1}
        iterutils.merge_into_dict(d, {'foo': 2})
        self.assertEqual(d, {'foo': 2})

    def test_merge_several(self):
        d = {'foo': 1}
        iterutils.merge_into_dict(d, {'bar': 2}, {'baz': 3})
        self.assertEqual(d, {'foo': 1, 'bar': 2, 'baz': 3})

        d = {'foo': 1}
        iterutils.merge_into_dict(d, {'foo': 2}, {'foo': 3})
        self.assertEqual(d, {'foo': 3})

    def test_merge_lists(self):
        d = {'foo': [1]}
        iterutils.merge_into_dict(d, {'foo': [2]})
        self.assertEqual(d, {'foo': [1, 2]})


class TestMergeDicts(TestCase):
    def test_merge_empty(self):
        self.assertEqual(iterutils.merge_dicts({}, {}), {})
        self.assertEqual(iterutils.merge_dicts({}, {'foo': 1}), {'foo': 1})
        self.assertEqual(iterutils.merge_dicts({'foo': 1}, {}), {'foo': 1})

    def test_merge_none(self):
        self.assertEqual(iterutils.merge_dicts({'foo': None}, {'foo': 1}),
                         {'foo': 1})
        self.assertEqual(iterutils.merge_dicts({'foo': 1}, {'foo': None}),
                         {'foo': 1})

        self.assertEqual(iterutils.merge_dicts({'foo': None}, {'bar': 1}),
                         {'foo': None, 'bar': 1})
        self.assertEqual(iterutils.merge_dicts({'foo': 1}, {'bar': None}),
                         {'foo': 1, 'bar': None})

    def test_merge_single(self):
        self.assertEqual(iterutils.merge_dicts({'foo': 1}, {'foo': 2}),
                         {'foo': 2})

    def test_merge_list(self):
        self.assertEqual(iterutils.merge_dicts({'foo': [1]}, {'foo': [2]}),
                         {'foo': [1, 2]})

    def test_merge_dict(self):
        self.assertEqual(iterutils.merge_dicts(
            {'foo': {'bar': [1], 'baz': 2}},
            {'foo': {'bar': [2], 'quux': 3}}
        ), {'foo': {'bar': [1, 2], 'baz': 2, 'quux': 3}})

    def test_merge_incompatible(self):
        merge_dicts = iterutils.merge_dicts
        self.assertRaises(TypeError, merge_dicts, {'foo': 1}, {'foo': [2]})
        self.assertRaises(TypeError, merge_dicts, {'foo': [1]}, {'foo': 2})
        self.assertRaises(TypeError, merge_dicts, {'foo': {}}, {'foo': 2})
        self.assertRaises(TypeError, merge_dicts, {'foo': 1}, {'foo': {}})

    def test_merge_several(self):
        merge_dicts = iterutils.merge_dicts
        self.assertEqual(merge_dicts({}, {}, {}), {})
        self.assertEqual(merge_dicts({'foo': 1}, {'bar': 2}, {'baz': 3}),
                         {'foo': 1, 'bar': 2, 'baz': 3})
        self.assertEqual(merge_dicts({'foo': 1}, {'foo': 2, 'bar': 3},
                                     {'baz': 4}),
                         {'foo': 2, 'bar': 3, 'baz': 4})

    def test_merge_makes_copies(self):
        d = {'foo': [1]}
        self.assertEqual(iterutils.merge_dicts({}, d, {'foo': [2]}),
                         {'foo': [1, 2]})
        self.assertEqual(d, {'foo': [1]})


class TestSliceDict(TestCase):
    def test_present(self):
        d = {'foo': 1, 'bar': 2, 'baz': 3}
        self.assertEqual(iterutils.slice_dict(d, ['foo', 'bar']),
                         {'foo': 1, 'bar': 2})
        self.assertEqual(d, {'baz': 3})

    def test_not_present(self):
        d = {'foo': 1, 'bar': 2, 'baz': 3}
        self.assertEqual(iterutils.slice_dict(d, ['foo', 'quux']),
                         {'foo': 1})
        self.assertEqual(d, {'bar': 2, 'baz': 3})
