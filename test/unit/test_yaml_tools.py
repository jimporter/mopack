import yaml
from io import StringIO
from textwrap import dedent
from unittest import mock, TestCase
from yaml.error import MarkedYAMLError

from mopack.yaml_tools import *


class TestMakeParseError(TestCase):
    def test_make(self):
        data = StringIO('&')
        try:
            yaml.safe_load(data)
        except MarkedYAMLError as e:
            err = make_parse_error(e, data)
            self.assertEqual(err.snippet, '&')
            self.assertEqual(err.mark.line, 0)
            self.assertEqual(err.mark.column, 1)
            self.assertRegex(str(err), '(?m)^  &\n   \\^$')


class TestLoadFile(TestCase):
    yaml_data = dedent("""
    house:
      cat: 1
      dog: 2
    zoo:
      panda: 3
      giraffe: 4
    """).strip()

    def test_success(self):
        mopen = mock.mock_open(read_data=self.yaml_data)
        with mock.patch('builtins.open', mopen):
            with load_file('file.yml') as data:
                self.assertEqual(data, {'house': {'cat': 1, 'dog': 2},
                                        'zoo': {'panda': 3, 'giraffe': 4}})

    def test_parse_error(self):
        with mock.patch('builtins.open', mock.mock_open(read_data='&')), \
             self.assertRaises(YamlParseError):  # noqa
            with load_file('file.yml'):
                pass

    def test_user_error(self):
        mopen = mock.mock_open(read_data=self.yaml_data)
        with mock.patch('builtins.open', mopen), \
             self.assertRaises(YamlParseError):  # noqa
            with load_file('file.yml', Loader=SafeLineLoader) as data:
                raise MarkedYAMLError('context', data.mark.start, 'problem',
                                      data.marks['zoo'].start)


class TestMarkedList(TestCase):
    def test_init(self):
        m = MarkedList()
        self.assertEqual(m, [])
        self.assertEqual(m.mark, None)
        self.assertEqual(m.marks, [])
        self.assertEqual(m.value_marks, [])

        m = MarkedList('mark')
        self.assertEqual(m, [])
        self.assertEqual(m.mark, 'mark')
        self.assertEqual(m.marks, [])
        self.assertEqual(m.value_marks, [])

    def test_append(self):
        m = MarkedList()
        m.append(1, 'mark1')
        self.assertEqual(m, [1])
        self.assertEqual(m.marks, ['mark1'])
        self.assertEqual(m.value_marks, ['mark1'])

        m[-1:] = [1, 2, 3]
        self.assertEqual(m, [1, 2, 3])
        self.assertEqual(m.marks, ['mark1'])
        self.assertEqual(m.value_marks, ['mark1'])

        m.append(4, 'mark4')
        self.assertEqual(m, [1, 2, 3, 4])
        self.assertEqual(m.marks, ['mark1', None, None, 'mark4'])
        self.assertEqual(m.value_marks, ['mark1', None, None, 'mark4'])

    def test_extend(self):
        m = MarkedList()
        m.extend([1, 2, 3])
        self.assertEqual(m, [1, 2, 3])
        self.assertEqual(m.mark, None)
        self.assertEqual(m.marks, [None, None, None])
        self.assertEqual(m.value_marks, [None, None, None])

        m2 = MarkedList('mark')
        m2.append(4, 'mark4')
        m.extend(m2)
        self.assertEqual(m, [1, 2, 3, 4])
        self.assertEqual(m.mark, 'mark')
        self.assertEqual(m.marks, [None, None, None, 'mark4'])
        self.assertEqual(m.value_marks, [None, None, None, 'mark4'])

        m3 = MarkedList('badmark')
        m.extend(m3)
        self.assertEqual(m, [1, 2, 3, 4])
        self.assertEqual(m.mark, 'mark')
        self.assertEqual(m.marks, [None, None, None, 'mark4'])
        self.assertEqual(m.value_marks, [None, None, None, 'mark4'])

    def test_copy(self):
        m = MarkedList('mark')
        m.append(1, 'mark1')

        m2 = m.copy()
        self.assertEqual(m2, [1])
        self.assertEqual(m2.mark, 'mark')
        self.assertEqual(m2.marks, ['mark1'])
        self.assertEqual(m2.value_marks, ['mark1'])


class TestMarkedDict(TestCase):
    def test_init(self):
        m = MarkedDict()
        self.assertEqual(m, {})
        self.assertEqual(m.mark, None)
        self.assertEqual(m.marks, {})
        self.assertEqual(m.value_marks, {})

        m = MarkedDict('mark')
        self.assertEqual(m, {})
        self.assertEqual(m.mark, 'mark')
        self.assertEqual(m.marks, {})
        self.assertEqual(m.value_marks, {})

    def test_add(self):
        m = MarkedDict()
        m.add('key1', 1, 'kmark1', 'vmark1')
        self.assertEqual(m, {'key1': 1})
        self.assertEqual(m.marks, {'key1': 'kmark1'})
        self.assertEqual(m.value_marks, {'key1': 'vmark1'})

        m.add('key2', 2)
        self.assertEqual(m, {'key1': 1, 'key2': 2})
        self.assertEqual(m.marks, {'key1': 'kmark1'})
        self.assertEqual(m.value_marks, {'key1': 'vmark1'})

    def test_pop(self):
        m = MarkedDict()
        m.add('key1', 1, 'mark1')

        self.assertEqual(m.pop('key1'), 1)
        self.assertEqual(m, {})
        self.assertEqual(m.marks, {})
        self.assertEqual(m.value_marks, {})

        self.assertEqual(m.pop('key2', 2), 2)
        with self.assertRaises(KeyError):
            m.pop('key2')

    def test_update(self):
        m = MarkedDict()
        m.update({'key1': 1, 'key2': 2})
        self.assertEqual(m, {'key1': 1, 'key2': 2})
        self.assertEqual(m.mark, None)
        self.assertEqual(m.marks, {})
        self.assertEqual(m.value_marks, {})

        m2 = MarkedDict('mark')
        m.add('key3', 3, 'kmark3', 'vmark3')
        m.update(m2)
        self.assertEqual(m, {'key1': 1, 'key2': 2, 'key3': 3})
        self.assertEqual(m.mark, 'mark')
        self.assertEqual(m.marks, {'key3': 'kmark3'})
        self.assertEqual(m.value_marks, {'key3': 'vmark3'})

        m3 = MarkedDict('badmark')
        m.update(m3)
        self.assertEqual(m, {'key1': 1, 'key2': 2, 'key3': 3})
        self.assertEqual(m.mark, 'mark')
        self.assertEqual(m.marks, {'key3': 'kmark3'})
        self.assertEqual(m.value_marks, {'key3': 'vmark3'})

    def test_update_kwargs(self):
        m = MarkedDict()
        m.update(key1=1, key2=2)
        self.assertEqual(m, {'key1': 1, 'key2': 2})
        self.assertEqual(m.mark, None)
        self.assertEqual(m.marks, {})
        self.assertEqual(m.value_marks, {})

    def test_copy(self):
        m = MarkedDict('mark')
        m.add('key1', 1, 'kmark1', 'vmark1')

        m2 = m.copy()
        self.assertEqual(m2, {'key1': 1})
        self.assertEqual(m2.mark, 'mark')
        self.assertEqual(m2.marks, {'key1': 'kmark1'})
        self.assertEqual(m2.value_marks, {'key1': 'vmark1'})


class TestSafeLineLoader(TestCase):
    def assertMark(self, mark_range, start, end):
        self.assertEqual([(i.line, i.column) for i in mark_range],
                         [start, end])

    def assertMarkDicts(self, marks, expected):
        self.assertEqual({k: [(m.line, m.column) for m in v]
                          for k, v in marks.items()}, expected)

    def assertMarkLists(self, marks, expected):
        self.assertEqual([[(m.line, m.column) for m in i] for i in marks],
                         expected)

    def test_mapping(self):
        data = yaml.load(dedent("""
        house:
          cat: 1
          dog: 2
        zoo:
          panda: 3
          giraffe: 4
        """).strip(), Loader=SafeLineLoader)

        self.assertEqual(data, {'house': {'cat': 1, 'dog': 2},
                                'zoo': {'panda': 3, 'giraffe': 4}})

        self.assertMark(data.mark, (0, 0), (5, 12))
        self.assertMarkDicts(data.marks,
                             {'house': [(0, 0), (0, 5)],
                              'zoo':   [(3, 0), (3, 3)]})
        self.assertMarkDicts(data.value_marks,
                             {'house': [(1, 2), (3,  0)],
                              'zoo':   [(4, 2), (5, 12)]})

        self.assertMark(data['house'].mark, (1, 2), (3, 0))
        self.assertMarkDicts(data['house'].marks,
                             {'cat': [(1, 2), (1, 5)],
                              'dog': [(2, 2), (2, 5)]})
        self.assertMarkDicts(data['house'].value_marks,
                             {'cat': [(1, 7), (1, 8)],
                              'dog': [(2, 7), (2, 8)]})

        self.assertMark(data['zoo'].mark, (4, 2), (5, 12))
        self.assertMarkDicts(data['zoo'].marks,
                             {'panda':   [(4, 2), (4, 7)],
                              'giraffe': [(5, 2), (5, 9)]})
        self.assertMarkDicts(data['zoo'].value_marks,
                             {'panda':   [(4,  9), (4, 10)],
                              'giraffe': [(5, 11), (5, 12)]})

    def test_sequence(self):
        data = yaml.load(dedent("""
        - - A1
          - A2
        - - B1
          - B2
        """).strip(), Loader=SafeLineLoader)

        self.assertEqual(data, [['A1', 'A2'], ['B1', 'B2']])

        self.assertMark(data.mark, (0, 0), (3, 6))
        self.assertMarkLists(data.marks,
                             [[(0, 2), (2, 0)],
                              [(2, 2), (3, 6)]])

        self.assertMark(data[0].mark, (0, 2), (2, 0))
        self.assertMarkLists(data[0].marks,
                             [[(0, 4), (0, 6)],
                              [(1, 4), (1, 6)]])

        self.assertMark(data[1].mark, (2, 2), (3, 6))
        self.assertMarkLists(data[1].marks,
                             [[(2, 4), (2, 6)],
                              [(3, 4), (3, 6)]])
