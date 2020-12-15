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
                raise MarkedYAMLError('context', data.mark, 'problem',
                                      data.marks['zoo'])


class TestMarkedList(TestCase):
    def test_init(self):
        m = MarkedList()
        self.assertEqual(m, [])
        self.assertEqual(m.mark, None)
        self.assertEqual(m.marks, [])

        m = MarkedList('mark')
        self.assertEqual(m, [])
        self.assertEqual(m.mark, 'mark')
        self.assertEqual(m.marks, [])

    def test_append(self):
        m = MarkedList()
        m.append(1, 'mark1')
        self.assertEqual(m, [1])
        self.assertEqual(m.marks, ['mark1'])

        m[-1:] = [1, 2, 3]
        self.assertEqual(m, [1, 2, 3])
        self.assertEqual(m.marks, ['mark1'])

        m.append(4, 'mark4')
        self.assertEqual(m, [1, 2, 3, 4])
        self.assertEqual(m.marks, ['mark1', None, None, 'mark4'])

    def test_extend(self):
        m = MarkedList()
        m.extend([1, 2, 3])
        self.assertEqual(m, [1, 2, 3])
        self.assertEqual(m.mark, None)
        self.assertEqual(m.marks, [None, None, None])

        m2 = MarkedList('mark')
        m2.append(4, 'mark4')
        m.extend(m2)
        self.assertEqual(m, [1, 2, 3, 4])
        self.assertEqual(m.mark, 'mark')
        self.assertEqual(m.marks, [None, None, None, 'mark4'])

        m3 = MarkedList('badmark')
        m.extend(m3)
        self.assertEqual(m, [1, 2, 3, 4])
        self.assertEqual(m.mark, 'mark')
        self.assertEqual(m.marks, [None, None, None, 'mark4'])

    def test_copy(self):
        m = MarkedList('mark')
        m.append(1, 'mark1')

        m2 = m.copy()
        self.assertEqual(m2, [1])
        self.assertEqual(m2.mark, 'mark')
        self.assertEqual(m2.marks, ['mark1'])


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

        self.assertEqual(data.mark.line, 0)
        self.assertEqual(data.mark.column, 0)
        self.assertEqual({k: (v.line, v.column)
                          for k, v in data.marks.items()},
                         {'house': (0, 0), 'zoo': (3, 0)})
        self.assertEqual({k: (v.line, v.column)
                          for k, v in data.value_marks.items()},
                         {'house': (1, 2), 'zoo': (4, 2)})

        self.assertEqual(data['house'].mark.line, 1)
        self.assertEqual(data['house'].mark.column, 2)
        self.assertEqual({k: (v.line, v.column)
                          for k, v in data['house'].marks.items()},
                         {'cat': (1, 2), 'dog': (2, 2)})
        self.assertEqual({k: (v.line, v.column)
                          for k, v in data['house'].value_marks.items()},
                         {'cat': (1, 7), 'dog': (2, 7)})

        self.assertEqual(data['zoo'].mark.line, 4)
        self.assertEqual(data['zoo'].mark.column, 2)
        self.assertEqual({k: (v.line, v.column)
                          for k, v in data['zoo'].marks.items()},
                         {'panda': (4, 2), 'giraffe': (5, 2)})
        self.assertEqual({k: (v.line, v.column)
                          for k, v in data['zoo'].value_marks.items()},
                         {'panda': (4, 9), 'giraffe': (5, 11)})

    def test_sequence(self):
        data = yaml.load(dedent("""
        - - A1
          - A2
        - - B1
          - B2
        """).strip(), Loader=SafeLineLoader)

        self.assertEqual(data, [['A1', 'A2'], ['B1', 'B2']])

        self.assertEqual(data.mark.line, 0)
        self.assertEqual(data.mark.column, 0)
        self.assertEqual([(i.line, i.column) for i in data.marks],
                         [(0, 2), (2, 2)])

        self.assertEqual(data[0].mark.line, 0)
        self.assertEqual(data[0].mark.column, 2)
        self.assertEqual([(i.line, i.column) for i in data[0].marks],
                         [(0, 4), (1, 4)])

        self.assertEqual(data[1].mark.line, 2)
        self.assertEqual(data[1].mark.column, 2)
        self.assertEqual([(i.line, i.column) for i in data[1].marks],
                         [(2, 4), (3, 4)])
