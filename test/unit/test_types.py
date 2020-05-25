import ntpath
import posixpath
from unittest import mock, TestCase

from mopack.types import *


def integer(field, value):
    if not isinstance(value, int):
        raise FieldError('expected an integer', field)
    return value


class TestMaybe(TestCase):
    def test_basic(self):
        self.assertEqual(maybe(string)('field', None), None)
        self.assertEqual(maybe(string)('field', 'foo'), 'foo')

    def test_default(self):
        self.assertEqual(maybe(string, 'default')('field', None), 'default')
        self.assertEqual(maybe(string, 'default')('field', 'foo'), 'foo')

    def test_invalid(self):
        self.assertRaises(FieldError, maybe(string), 'field', 1)


class TestOneOf(TestCase):
    def setUp(self):
        self.one_of = one_of(string, integer, desc='str or int')

    def test_valid(self):
        self.assertEqual(self.one_of('field', 'foo'), 'foo')
        self.assertEqual(self.one_of('field', 1), 1)

    def test_invalid(self):
        self.assertRaises(FieldError, self.one_of, 'field', None)


class TestConstant(TestCase):
    def setUp(self):
        self.constant = constant('foo', 'bar')

    def test_valid(self):
        self.assertEqual(self.constant('field', 'foo'), 'foo')
        self.assertEqual(self.constant('field', 'bar'), 'bar')

    def test_invalid(self):
        self.assertRaises(FieldError, self.constant, 'field', 'baz')
        self.assertRaises(FieldError, self.constant, 'field', None)


class TestListOf(TestCase):
    def test_list(self):
        checker = list_of(string)
        self.assertEqual(checker('field', []), [])
        self.assertEqual(checker('field', ['foo']), ['foo'])
        self.assertEqual(checker('field', ['foo', 'bar']), ['foo', 'bar'])

    def test_listify(self):
        checker = list_of(string, listify=True)
        self.assertEqual(checker('field', []), [])
        self.assertEqual(checker('field', ['foo']), ['foo'])
        self.assertEqual(checker('field', ['foo', 'bar']), ['foo', 'bar'])
        self.assertEqual(checker('field', None), [])
        self.assertEqual(checker('field', 'foo'), ['foo'])

    def test_invalid(self):
        self.assertRaises(FieldError, list_of(string), 'field', None)
        self.assertRaises(FieldError, list_of(string), 'field', 'foo')
        self.assertRaises(FieldError, list_of(string), 'field', {})


class TestDictShape(TestCase):
    def setUp(self):
        self.dict_shape = dict_shape({'foo': string}, 'foo dict')

    def test_valid(self):
        self.assertEqual(self.dict_shape('field', {'foo': 'bar'}),
                         {'foo': 'bar'})

    def test_invalid_keys(self):
        self.assertRaises(FieldError, self.dict_shape, 'field', {})
        self.assertRaises(FieldError, self.dict_shape, 'field', {'bar': 'b'})
        self.assertRaises(FieldError, self.dict_shape, 'field',
                          {'foo': 'f', 'bar': 'b'})

    def test_invalid_values(self):
        self.assertRaises(FieldError, self.dict_shape, 'field', {'foo': 1})


class TestInnerPath(TestCase):
    def test_valid(self):
        self.assertEqual(inner_path('field', 'path'), 'path')
        self.assertEqual(inner_path('field', 'path/..'), '.')
        self.assertEqual(inner_path('field', 'foo/../bar'), 'bar')

    def test_outer(self):
        self.assertRaises(FieldError, inner_path, 'field', '../path')
        self.assertRaises(FieldError, inner_path, 'field', 'path/../..')

    def test_absolute_posix(self):
        with mock.patch('os.path', posixpath):
            self.assertRaises(FieldError, inner_path, 'field', '/path')

    def test_absolute_nt(self):
        with mock.patch('os.path', ntpath):
            self.assertRaises(FieldError, inner_path, 'field', '/path')
            self.assertRaises(FieldError, inner_path, 'field', 'C:path')
            self.assertRaises(FieldError, inner_path, 'field', 'C:\\path')
            self.assertRaises(FieldError, inner_path, 'field', 'C:')


class TestShellArgs(TestCase):
    def test_single(self):
        self.assertEqual(shell_args()('field', 'foo'), ['foo'])

    def test_multiple(self):
        self.assertEqual(shell_args()('field', 'foo bar baz'),
                         ['foo', 'bar', 'baz'])

    def test_quote(self):
        self.assertEqual(shell_args()('field', 'foo "bar baz"'),
                         ['foo', 'bar baz'])
        self.assertEqual(shell_args()('field', 'foo"bar baz"'), ['foobar baz'])

    def test_type(self):
        self.assertEqual(shell_args(type=tuple)('field', 'foo bar baz'),
                         ('foo', 'bar', 'baz'))

    def test_escapes(self):
        self.assertEqual(shell_args()('field', 'foo\\ bar'), ['foo\\', 'bar'])
        self.assertEqual(shell_args(escapes=True)('field', 'foo\\ bar'),
                         ['foo bar'])

    def test_invalid(self):
        self.assertRaises(FieldError, shell_args(), 'field', 1)
