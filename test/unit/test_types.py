import ntpath
import os
import posixpath
from contextlib import contextmanager
from unittest import mock, TestCase

from mopack.types import *
from mopack.yaml_tools import load_file, SafeLineLoader


class TypeTestCase(TestCase):
    @contextmanager
    def assertFieldError(self, field, regex=None):
        ctx = (self.assertRaises(FieldError) if regex is None else
               self.assertRaisesRegex(FieldError, regex))
        with ctx as raised:
            yield raised
        self.assertEqual(raised.exception.field, field)


class TestMaybe(TypeTestCase):
    def test_basic(self):
        self.assertEqual(maybe(string)('field', None), None)
        self.assertEqual(maybe(string)('field', 'foo'), 'foo')

    def test_default(self):
        self.assertEqual(maybe(string, 'default')('field', None), 'default')
        self.assertEqual(maybe(string, 'default')('field', 'foo'), 'foo')

    def test_invalid(self):
        with self.assertFieldError(('field',)):
            maybe(string)('field', 1)


class TestDefault(TypeTestCase):
    def test_basic(self):
        self.assertEqual(default(string)('field', Unset), None)
        self.assertEqual(default(string)('field', 'foo'), 'foo')

    def test_default(self):
        self.assertEqual(default(string, 'default')('field', Unset), 'default')
        self.assertEqual(default(string, 'default')('field', 'foo'), 'foo')

    def test_invalid(self):
        with self.assertFieldError(('field',)):
            default(string)('field', 1)


class TestOneOf(TypeTestCase):
    def setUp(self):
        self.one_of = one_of(string, boolean, desc='str or bool')

    def test_valid(self):
        self.assertEqual(self.one_of('field', 'foo'), 'foo')
        self.assertEqual(self.one_of('field', True), True)

    def test_invalid(self):
        with self.assertFieldError(('field',)):
            self.one_of('field', 1)


class TestConstant(TypeTestCase):
    def setUp(self):
        self.constant = constant('foo', 'bar')

    def test_valid(self):
        self.assertEqual(self.constant('field', 'foo'), 'foo')
        self.assertEqual(self.constant('field', 'bar'), 'bar')

    def test_invalid(self):
        with self.assertFieldError(('field',)):
            self.constant('field', 'baz')
        with self.assertFieldError(('field',)):
            self.constant('field', None)


class TestListOf(TypeTestCase):
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
        with self.assertFieldError(('field',), 'expected a list'):
            list_of(string)('field', None)
        with self.assertFieldError(('field',), 'expected a list'):
            list_of(string)('field', 'foo')
        with self.assertFieldError(('field',), 'expected a list'):
            list_of(string)('field', {})
        with self.assertFieldError(('field', 0), 'expected a string'):
            list_of(string)('field', [1])


class TestDictOf(TypeTestCase):
    def test_dict(self):
        checker = dict_of(string, string)
        self.assertEqual(checker('field', {}), {})
        self.assertEqual(checker('field', {'f': 'foo'}), {'f': 'foo'})
        self.assertEqual(checker('field', {'f': 'foo', 'b': 'bar'}),
                         {'f': 'foo', 'b': 'bar'})

    def test_invalid_type(self):
        with self.assertFieldError(('field',), 'expected a dict'):
            dict_of(string, string)('field', None)
        with self.assertFieldError(('field',), 'expected a dict'):
            dict_of(string, string)('field', 'foo')
        with self.assertFieldError(('field',), 'expected a dict'):
            dict_of(string, string)('field', [])

    def test_invalid_key(self):
        with self.assertFieldError(('field', 1), 'expected a string'):
            dict_of(string, boolean)('field', {1: True})
        with self.assertFieldError(('field', 1), 'expected a string'):
            dict_of(string, boolean)('field', {1: 'foo'})

    def test_invalid_value(self):
        with self.assertFieldError(('field', 'f'), 'expected a boolean'):
            print(dict_of(string, boolean)('field', {'f': 'foo'}))


class TestDictShape(TypeTestCase):
    def setUp(self):
        self.dict_shape = dict_shape({'foo': string}, 'a foo dict')

    def test_valid(self):
        self.assertEqual(self.dict_shape('field', {'foo': 'bar'}),
                         {'foo': 'bar'})

    def test_invalid_type(self):
        with self.assertFieldError(('field',), 'expected a foo dict'):
            self.dict_shape('field', None)
        with self.assertFieldError(('field',), 'expected a foo dict'):
            self.dict_shape('field', 'foo')
        with self.assertFieldError(('field',), 'expected a foo dict'):
            self.dict_shape('field', [])

    def test_invalid_keys(self):
        with self.assertFieldError(('field',), 'expected a foo dict'):
            self.dict_shape('field', {})
        with self.assertFieldError(('field', 'bar'), 'unexpected key'):
            self.dict_shape('field', {'bar': 'b'})
        with self.assertFieldError(('field', 'bar'), 'unexpected key'):
            self.dict_shape('field', {'foo': 'f', 'bar': 'b'})

    def test_invalid_values(self):
        with self.assertFieldError(('field', 'foo'), 'expected a string'):
            self.dict_shape('field', {'foo': 1})


class TestString(TypeTestCase):
    def test_valid(self):
        self.assertEqual(string('field', 'foo'), 'foo')
        self.assertEqual(string('field', 'bar'), 'bar')

    def test_invalid(self):
        with self.assertFieldError(('field',)):
            string('field', 1)
        with self.assertFieldError(('field',)):
            string('field', None)


class TestBoolean(TypeTestCase):
    def test_valid(self):
        self.assertEqual(boolean('field', True), True)
        self.assertEqual(boolean('field', False), False)

    def test_invalid(self):
        with self.assertFieldError(('field',)):
            boolean('field', 1)
        with self.assertFieldError(('field',)):
            boolean('field', None)


class TestInnerPath(TypeTestCase):
    def test_valid(self):
        self.assertEqual(inner_path('field', 'path'), 'path')
        self.assertEqual(inner_path('field', 'path/..'), '.')
        self.assertEqual(inner_path('field', 'foo/../bar'), 'bar')

    def test_outer(self):
        with self.assertFieldError(('field',)):
            inner_path('field', '../path')
        with self.assertFieldError(('field',)):
            inner_path('field', 'path/../..')

    def test_absolute_posix(self):
        with mock.patch('os.path', posixpath):
            with self.assertFieldError(('field',)):
                inner_path('field', '/path')

    def test_absolute_nt(self):
        with mock.patch('os.path', ntpath):
            with self.assertFieldError(('field',)):
                inner_path('field', '/path')
            with self.assertFieldError(('field',)):
                inner_path('field', 'C:path')
            with self.assertFieldError(('field',)):
                inner_path('field', 'C:\\path')
            with self.assertFieldError(('field',)):
                inner_path('field', 'C:')


class TestAbsOrInnerPath(TypeTestCase):
    def test_inner(self):
        self.assertEqual(abs_or_inner_path('field', 'path'), 'path')
        self.assertEqual(abs_or_inner_path('field', 'path/..'), '.')
        self.assertEqual(abs_or_inner_path('field', 'foo/../bar'), 'bar')

    def test_outer(self):
        with self.assertFieldError(('field',)):
            abs_or_inner_path('field', '../path')
        with self.assertFieldError(('field',)):
            abs_or_inner_path('field', 'path/../..')

    def test_absolute_posix(self):
        with mock.patch('os.path', posixpath):
            self.assertEqual(abs_or_inner_path('field', '/path'), '/path')

    def test_absolute_nt(self):
        with mock.patch('os.path', ntpath):
            self.assertEqual(abs_or_inner_path('field', '/path'), '\\path')
            self.assertEqual(abs_or_inner_path('field', 'C:\\path'),
                             'C:\\path')
            self.assertEqual(abs_or_inner_path('field', 'C:'), 'C:')
            self.assertEqual(abs_or_inner_path('field', 'C:path'), 'C:path')


class TestAnyPath(TypeTestCase):
    def test_relative(self):
        self.assertEqual(any_path()('field', 'path'), 'path')
        self.assertEqual(any_path()('field', '../path'),
                         os.path.join('..', 'path'))
        self.assertEqual(any_path()('field', 'foo/../bar'), 'bar')
        self.assertEqual(any_path('/base')('field', 'path'),
                         os.sep + os.path.join('base', 'path'))

    def test_absolute(self):
        self.assertEqual(any_path()('field', '/path'), os.sep + 'path')
        self.assertEqual(any_path('/base')('field', '/path'), os.sep + 'path')


class TestSshPath(TypeTestCase):
    def test_valid(self):
        urls = ['server:.',
                'user@server:~',
                'git@github.com:user/repo.git']
        for i in urls:
            self.assertEqual(ssh_path('field', i), i)

    def test_invalid(self):
        with self.assertFieldError(('field',)):
            ssh_path('field', 'path')


class TestUrl(TypeTestCase):
    def test_valid(self):
        urls = ['http://localhost',
                'http://user:pass@localhost',
                'http://localhost:1234',
                'http://localhost/path?query#anchor',
                'http://user:pass@example.com:1234/path?query#anchor']
        for i in urls:
            self.assertEqual(url('field', i), i)

    def test_invalid(self):
        not_urls = ['path',
                    'http:localhost',
                    'http://localhost:foo',
                    'http://localhost:1234foo']
        for i in not_urls:
            with self.assertFieldError(('field',)):
                url('field', i)


class TestShellArgs(TypeTestCase):
    def test_single(self):
        self.assertEqual(shell_args()('field', 'foo'), ['foo'])

    def test_multiple(self):
        self.assertEqual(shell_args()('field', 'foo bar baz'),
                         ['foo', 'bar', 'baz'])

    def test_quote(self):
        self.assertEqual(shell_args()('field', 'foo "bar baz"'),
                         ['foo', 'bar baz'])
        self.assertEqual(shell_args()('field', 'foo"bar baz"'), ['foobar baz'])

    def test_list(self):
        self.assertEqual(shell_args()('field', ['foo', 'bar baz']),
                         ['foo', 'bar baz'])

    def test_empty(self):
        self.assertEqual(shell_args()('field', ''), [])
        self.assertEqual(shell_args()('field', []), [])
        self.assertEqual(shell_args()('field', None), [])

    def test_type(self):
        self.assertEqual(shell_args(type=tuple)('field', 'foo bar baz'),
                         ('foo', 'bar', 'baz'))

    def test_escapes(self):
        self.assertEqual(shell_args()('field', 'foo\\ bar'), ['foo\\', 'bar'])
        self.assertEqual(shell_args(escapes=True)('field', 'foo\\ bar'),
                         ['foo bar'])

    def test_invalid(self):
        with self.assertFieldError(('field',)):
            shell_args()('field', 1)


class TestTryLoadConfig(TestCase):
    def load_data(self, data, Loader=SafeLineLoader):
        with mock.patch('builtins.open', mock.mock_open(read_data=data)):
            with load_file('file.yml', Loader=Loader) as f:
                return f

    def test_single_field(self):
        cfg = self.load_data('foo: Foo\nbar: Bar\n')
        with self.assertRaisesRegex(MarkedYAMLError,
                                    '^context\n' +
                                    'expected a boolean\n' +
                                    '  in ".*", line 1, column 1$'):
            with try_load_config(cfg, 'context'):
                boolean('foo', cfg['foo'])

    def test_multiple_fields(self):
        cfg = self.load_data('foo:\n  bar: Bar\n')
        with self.assertRaisesRegex(MarkedYAMLError,
                                    '^context\n' +
                                    '  in ".*", line 1, column 1\n' +
                                    'expected a boolean\n' +
                                    '  in ".*", line 2, column 3$'):
            with try_load_config(cfg, 'context'):
                dict_shape({'bar': boolean}, 'a bar dict')('foo', cfg['foo'])
