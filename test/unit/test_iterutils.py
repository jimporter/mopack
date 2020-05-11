from unittest import TestCase

from mopack import iterutils


class TestIsIterable(TestCase):
    def test_list(self):
        self.assertTrue(iterutils.isiterable([]))

    def test_dict(self):
        self.assertTrue(iterutils.isiterable([]))

    def test_generator(self):
        gen = (i for i in range(10))
        self.assertTrue(iterutils.isiterable(gen))

    def test_string(self):
        self.assertFalse(iterutils.isiterable('foo'))

    def test_none(self):
        self.assertFalse(iterutils.isiterable(None))


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
