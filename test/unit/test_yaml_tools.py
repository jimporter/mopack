import re
import yaml
from io import StringIO
from textwrap import dedent
from unittest import mock, TestCase
from yaml.error import MarkedYAMLError

from . import mock_open_data

from mopack.yaml_tools import *
from mopack.yaml_tools import _get_offset_mark


class TestMakeParseError(TestCase):
    def assertError(self, e, linecol, snippet, caret):
        self.assertEqual((e.mark.line, e.mark.column), linecol)
        self.assertEqual(e.snippet, snippet)
        self.assertRegex(str(e), '(?m)^{}$'.format(re.escape(caret)))

    def test_simple(self):
        data = StringIO('&')
        with self.assertRaises(MarkedYAMLError) as c:
            yaml.safe_load(data)
        err = make_parse_error(c.exception, data)
        self.assertError(err, (0, 1), '&', '  &\n   ^')

    def test_offset_plain(self):
        data = StringIO(dedent("""\
          house:
            cat: meow
            dog: woof
        """))
        cfg = yaml.load(data, Loader=SafeLineLoader)
        e = MarkedYAMLOffsetError('context', cfg['house'].mark, 'problem',
                                  cfg['house'].value_marks['cat'], offset=2)
        err = make_parse_error(e, data)
        self.assertError(err, (1, 9), '  cat: meow',
                         '    cat: meow\n           ^')

    def test_offset_quoted(self):
        data = StringIO(dedent("""\
          house:
            cat: "meow"
            dog: "woof"
        """))
        cfg = yaml.load(data, Loader=SafeLineLoader)
        e = MarkedYAMLOffsetError('context', cfg['house'].mark, 'problem',
                                  cfg['house'].value_marks['cat'], offset=2)
        err = make_parse_error(e, data)
        self.assertError(err, (1, 10), '  cat: "meow"',
                         '    cat: "meow"\n            ^')

    def test_offset_quoted_multiline(self):
        data = StringIO(dedent("""\
          house:
            cat: "meow
              meow
              meow"
            dog: "woof"
        """))
        cfg = yaml.load(data, Loader=SafeLineLoader)

        # Error at start of second line.
        e = MarkedYAMLOffsetError('context', cfg['house'].mark, 'problem',
                                  cfg['house'].value_marks['cat'], offset=5)
        err = make_parse_error(e, data)
        self.assertError(err, (2, 4), '    meow', '      meow\n      ^')

        # Error midway through second line.
        e = MarkedYAMLOffsetError('context', cfg['house'].mark, 'problem',
                                  cfg['house'].value_marks['cat'], offset=7)
        err = make_parse_error(e, data)
        self.assertError(err, (2, 6), '    meow', '      meow\n        ^')

        # Error at start of third line.
        e = MarkedYAMLOffsetError('context', cfg['house'].mark, 'problem',
                                  cfg['house'].value_marks['cat'], offset=10)
        err = make_parse_error(e, data)
        self.assertError(err, (3, 4), '    meow"', '      meow"\n      ^')

    def test_offset_block(self):
        data = StringIO(dedent("""\
          house:
            cat: >
              meow
              meow
            dog: "woof"
        """))
        cfg = yaml.load(data, Loader=SafeLineLoader)

        # Error on first line of block.
        e = MarkedYAMLOffsetError('context', cfg['house'].mark, 'problem',
                                  cfg['house'].value_marks['cat'], offset=2)
        err = make_parse_error(e, data)
        self.assertError(err, (2, 6), '    meow', '      meow\n        ^')

        # Error on second line of block.
        e = MarkedYAMLOffsetError('context', cfg['house'].mark, 'problem',
                                  cfg['house'].value_marks['cat'], offset=5)
        err = make_parse_error(e, data)
        self.assertError(err, (3, 4), '    meow', '      meow\n      ^')

        # Error at end of block.
        e = MarkedYAMLOffsetError('context', cfg['house'].mark, 'problem',
                                  cfg['house'].value_marks['cat'], offset=12)
        err = make_parse_error(e, data)
        self.assertError(err, (4, 0), '', '  \n  ^')

    def test_offset_block_indent_level(self):
        data = StringIO(dedent("""\
          house:
            cat: >2
               meow
               meow
            dog: "woof"
        """))
        cfg = yaml.load(data, Loader=SafeLineLoader)

        # Error on first line of block.
        e = MarkedYAMLOffsetError('context', cfg['house'].mark, 'problem',
                                  cfg['house'].value_marks['cat'], offset=2)
        err = make_parse_error(e, data)
        self.assertError(err, (2, 6), '     meow', '       meow\n        ^')

        # Error on second line of block.
        e = MarkedYAMLOffsetError('context', cfg['house'].mark, 'problem',
                                  cfg['house'].value_marks['cat'], offset=6)
        err = make_parse_error(e, data)
        self.assertError(err, (3, 4), '     meow', '       meow\n      ^')

    def test_offset_anchor_alias(self):
        data = StringIO(dedent("""\
          house:
            cat: &anchor meow
            dog: *anchor
        """))
        cfg = yaml.load(data, Loader=SafeLineLoader)

        # Error on anchor line.
        e = MarkedYAMLOffsetError('context', cfg['house'].mark, 'problem',
                                  cfg['house'].value_marks['cat'], offset=2)
        err = make_parse_error(e, data)
        self.assertError(err, (1, 17), '  cat: &anchor meow',
                         '    cat: &anchor meow\n'
                         '                   ^')

        # Error on alias line.
        e = MarkedYAMLOffsetError('context', cfg['house'].mark, 'problem',
                                  cfg['house'].value_marks['dog'], offset=2)
        err = make_parse_error(e, data)
        self.assertError(err, (1, 17), '  cat: &anchor meow',
                         '    cat: &anchor meow\n'
                         '                   ^')

    def test_offset_anchor_block(self):
        data = StringIO(dedent("""\
          house:
            cat: &anchor >
              meow
              meow
            dog: *anchor
        """))
        cfg = yaml.load(data, Loader=SafeLineLoader)

        # Error on anchor line.
        e = MarkedYAMLOffsetError('context', cfg['house'].mark, 'problem',
                                  cfg['house'].value_marks['cat'], offset=2)
        err = make_parse_error(e, data)
        self.assertError(err, (2, 6), '    meow', '      meow\n        ^')

        # Error on alias line.
        e = MarkedYAMLOffsetError('context', cfg['house'].mark, 'problem',
                                  cfg['house'].value_marks['dog'], offset=2)
        err = make_parse_error(e, data)
        self.assertError(err, (2, 6), '    meow', '      meow\n        ^')


class TestLoadFile(TestCase):
    yaml_data = dedent("""\
      house:
        cat: 1
        dog: 2
      zoo:
        panda: 3
        giraffe: 4
    """)

    def test_success(self):
        mopen = mock_open_data(self.yaml_data)
        with mock.patch('builtins.open', mopen):
            with load_file('file.yml') as data:
                self.assertEqual(data, {'house': {'cat': 1, 'dog': 2},
                                        'zoo': {'panda': 3, 'giraffe': 4}})

    def test_parse_error(self):
        with mock.patch('builtins.open', mock_open_data('&')), \
             self.assertRaises(YamlParseError):  # noqa
            with load_file('file.yml'):
                pass

    def test_user_error(self):
        with mock.patch('builtins.open', mock_open_data(self.yaml_data)), \
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
        data = yaml.load(dedent("""\
          house:
            cat: 1
            dog: 2
          zoo:
            panda: 3
            giraffe: 4
        """), Loader=SafeLineLoader)

        self.assertEqual(data, {'house': {'cat': 1, 'dog': 2},
                                'zoo': {'panda': 3, 'giraffe': 4}})

        self.assertMark(data.mark, (0, 0), (6, 0))
        self.assertMarkDicts(data.marks,
                             {'house': [(0, 0), (0, 5)],
                              'zoo':   [(3, 0), (3, 3)]})
        self.assertMarkDicts(data.value_marks,
                             {'house': [(1, 2), (3, 0)],
                              'zoo':   [(4, 2), (6, 0)]})

        self.assertMark(data['house'].mark, (1, 2), (3, 0))
        self.assertMarkDicts(data['house'].marks,
                             {'cat': [(1, 2), (1, 5)],
                              'dog': [(2, 2), (2, 5)]})
        self.assertMarkDicts(data['house'].value_marks,
                             {'cat': [(1, 7), (1, 8)],
                              'dog': [(2, 7), (2, 8)]})

        self.assertMark(data['zoo'].mark, (4, 2), (6, 0))
        self.assertMarkDicts(data['zoo'].marks,
                             {'panda':   [(4, 2), (4, 7)],
                              'giraffe': [(5, 2), (5, 9)]})
        self.assertMarkDicts(data['zoo'].value_marks,
                             {'panda':   [(4,  9), (4, 10)],
                              'giraffe': [(5, 11), (5, 12)]})

    def test_sequence(self):
        data = yaml.load(dedent("""\
          - - A1
            - A2
          - - B1
            - B2
        """), Loader=SafeLineLoader)

        self.assertEqual(data, [['A1', 'A2'], ['B1', 'B2']])

        self.assertMark(data.mark, (0, 0), (4, 0))
        self.assertMarkLists(data.marks,
                             [[(0, 2), (2, 0)],
                              [(2, 2), (4, 0)]])

        self.assertMark(data[0].mark, (0, 2), (2, 0))
        self.assertMarkLists(data[0].marks,
                             [[(0, 4), (0, 6)],
                              [(1, 4), (1, 6)]])

        self.assertMark(data[1].mark, (2, 2), (4, 0))
        self.assertMarkLists(data[1].marks,
                             [[(2, 4), (2, 6)],
                              [(3, 4), (3, 6)]])


class TestGetOffsetMark(TestCase):
    def assertMark(self, mark, linecol, index):
        self.assertEqual((mark.line, mark.column), linecol)
        self.assertEqual(mark.index, index)

    def test_plain(self):
        data = 'meow'
        self.assertMark(_get_offset_mark(data, 0), (0, 0), 0)
        self.assertMark(_get_offset_mark(data, 2), (0, 2), 2)

        data = 'meow[meow]'
        self.assertMark(_get_offset_mark(data, 0), (0, 0), 0)
        self.assertMark(_get_offset_mark(data, 4), (0, 4), 4)

        data = 'meow\n  meow'
        self.assertMark(_get_offset_mark(data, 5), (1, 2), 7)

    def test_quoted(self):
        data = "'meow'"
        self.assertMark(_get_offset_mark(data, 0), (0, 1), 1)
        self.assertMark(_get_offset_mark(data, 2), (0, 3), 3)
        # Past the parsed string.
        self.assertMark(_get_offset_mark(data, 5), (0, 6), 6)

        data = '"meow"'
        self.assertMark(_get_offset_mark(data, 0), (0, 1), 1)
        self.assertMark(_get_offset_mark(data, 2), (0, 3), 3)

    def test_quoted_escape(self):
        data = "'meow \\ meow'"
        self.assertMark(_get_offset_mark(data, 0), (0, 1), 1)
        self.assertMark(_get_offset_mark(data, 5), (0, 6), 6)
        self.assertMark(_get_offset_mark(data, 7), (0, 8), 8)

        data = "'meow '' meow'"
        self.assertMark(_get_offset_mark(data, 0), (0, 1), 1)
        self.assertMark(_get_offset_mark(data, 5), (0, 6), 6)
        self.assertMark(_get_offset_mark(data, 7), (0, 9), 9)

        data = '"meow \\n meow"'
        self.assertMark(_get_offset_mark(data, 0), (0, 1), 1)
        self.assertMark(_get_offset_mark(data, 5), (0, 6), 6)
        self.assertMark(_get_offset_mark(data, 7), (0, 9), 9)

        data = '"meow \\x0a meow"'
        self.assertMark(_get_offset_mark(data, 0), (0, 1), 1)
        self.assertMark(_get_offset_mark(data, 5), (0, 6), 6)
        self.assertMark(_get_offset_mark(data, 7), (0, 11), 11)

        data = '"meow \\\n meow"'
        self.assertMark(_get_offset_mark(data, 0), (0, 1), 1)
        self.assertMark(_get_offset_mark(data, 5), (0, 6), 6)
        self.assertMark(_get_offset_mark(data, 7), (1, 2), 10)

    def test_quoted_multiline(self):
        data = "'meow\n  meow\n  meow'"
        self.assertMark(_get_offset_mark(data, 0), (0, 1), 1)
        self.assertMark(_get_offset_mark(data, 5), (1, 2), 8)
        self.assertMark(_get_offset_mark(data, 10), (2, 2), 15)
        self.assertMark(_get_offset_mark(data, 14), (2, 6), 19)
        # Past the parsed string.
        self.assertMark(_get_offset_mark(data, 15), (2, 7), 20)

    def test_block(self):
        data = dedent("""\
          >
            meow
            meow
        """)
        self.assertMark(_get_offset_mark(data, 0), (1, 2), 4)
        self.assertMark(_get_offset_mark(data, 3), (1, 5), 7)
        self.assertMark(_get_offset_mark(data, 4), (1, 6), 8)
        self.assertMark(_get_offset_mark(data, 5), (2, 2), 11)
        self.assertMark(_get_offset_mark(data, 8), (2, 5), 14)
        self.assertMark(_get_offset_mark(data, 9), (2, 6), 15)

        data = dedent("""\
          >
            meow

        """)
        self.assertMark(_get_offset_mark(data, 5), (3, 0), 10)

    def test_block_indent_level(self):
        data = dedent("""\
          >2
              meow
              meow
        """)
        self.assertMark(_get_offset_mark(data, 0), (1, 2), 5)
        self.assertMark(_get_offset_mark(data, 5), (1, 7), 10)
        self.assertMark(_get_offset_mark(data, 6), (1, 8), 11)
        self.assertMark(_get_offset_mark(data, 7), (2, 2), 14)
        self.assertMark(_get_offset_mark(data, 12), (2, 7), 19)
        self.assertMark(_get_offset_mark(data, 13), (2, 8), 20)

    def test_block_keep_newlines(self):
        data = dedent("""\
          |+
            meow


        """)
        self.assertMark(_get_offset_mark(data, 5), (4, 0), 12)

    def test_block_empty(self):
        data = dedent("""\
          >
        """)
        self.assertMark(_get_offset_mark(data, 0), (1, 0), 2)
        self.assertMark(_get_offset_mark(data, 1), (1, 0), 2)

    def test_anchor(self):
        data = '&anchor meow'
        self.assertMark(_get_offset_mark(data, 0), (0, 8), 8)
        self.assertMark(_get_offset_mark(data, 2), (0, 10), 10)

    def test_anchor_block(self):
        data = dedent("""\
          &anchor >
            meow
            meow
        """)
        self.assertMark(_get_offset_mark(data, 0), (1, 2), 12)
        self.assertMark(_get_offset_mark(data, 3), (1, 5), 15)
        self.assertMark(_get_offset_mark(data, 4), (1, 6), 16)
        self.assertMark(_get_offset_mark(data, 5), (2, 2), 19)
        self.assertMark(_get_offset_mark(data, 8), (2, 5), 22)
        self.assertMark(_get_offset_mark(data, 9), (2, 6), 23)
