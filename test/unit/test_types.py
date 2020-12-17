import ntpath
import os
import posixpath
from contextlib import contextmanager
from unittest import mock, TestCase

from mopack.placeholder import placeholder
from mopack.path import Path
from mopack.shell import ShellArguments
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


class TestTypeCheck(TypeTestCase):
    def test_object(self):
        class Thing:
            def __init__(self, field):
                T = TypeCheck(locals())
                T.field(string)

        self.assertEqual(Thing('foo').field, 'foo')
        with self.assertFieldError(('field',)):
            Thing(1)

    def test_object_extend(self):
        class Thing:
            def __init__(self):
                self.field = []

            def __call__(self, field):
                T = TypeCheck(locals())
                T.field(list_of(string, listify=True), extend=True)

        t = Thing()
        t('foo')
        t(['bar', 'baz'])
        self.assertEqual(t.field, ['foo', 'bar', 'baz'])
        with self.assertFieldError(('field',)):
            t(1)

    def test_dict(self):
        class Thing:
            def __init__(self, field):
                self.data = {}
                T = TypeCheck(locals())
                T.field(string, dest=self.data)

        self.assertEqual(Thing('foo').data['field'], 'foo')
        with self.assertFieldError(('field',)):
            Thing(1)

    def test_dict_extend(self):
        class Thing:
            def __init__(self):
                self.data = {'field': []}

            def __call__(self, field):
                T = TypeCheck(locals())
                T.field(list_of(string, listify=True), extend=True,
                        dest=self.data)

        t = Thing()
        t('foo')
        t(['bar', 'baz'])
        self.assertEqual(t.data['field'], ['foo', 'bar', 'baz'])
        with self.assertFieldError(('field',)):
            t(1)


class TestMaybe(TypeTestCase):
    def test_basic(self):
        self.assertEqual(maybe(string)('field', None), None)
        self.assertEqual(maybe(string)('field', Unset), None)
        self.assertEqual(maybe(string)('field', 'foo'), 'foo')

    def test_maybe(self):
        self.assertEqual(maybe(string, 'default')('field', None), 'default')
        self.assertEqual(maybe(string, 'default')('field', Unset), 'default')
        self.assertEqual(maybe(string, 'default')('field', 'foo'), 'foo')

    def test_empty(self):
        self.assertEqual(maybe(string, empty=1)('field', 'foo'), 'foo')
        self.assertEqual(maybe(string, empty=1)('field', 1), None)

        with self.assertFieldError(('field',)):
            maybe(string, empty=1)('field', None)
        with self.assertFieldError(('field',)):
            maybe(string, empty=1)('field', Unset)

    def test_invalid(self):
        with self.assertFieldError(('field',)):
            maybe(string)('field', 1)


class TestMaybeRaw(TypeTestCase):
    def test_basic(self):
        self.assertEqual(maybe_raw(string)('field', None), None)
        self.assertEqual(maybe_raw(string)('field', Unset), Unset)
        self.assertEqual(maybe_raw(string)('field', 'foo'), 'foo')

    def test_empty(self):
        self.assertEqual(maybe_raw(string, empty=1)('field', 'foo'), 'foo')
        self.assertEqual(maybe_raw(string, empty=1)('field', 1), 1)

        with self.assertFieldError(('field',)):
            maybe_raw(string, empty=1)('field', None)
        with self.assertFieldError(('field',)):
            maybe_raw(string, empty=1)('field', Unset)

    def test_invalid(self):
        with self.assertFieldError(('field',)):
            maybe_raw(string)('field', 1)


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
        with self.assertFieldError(('field',), 'expected a string'):
            list_of(string, listify=True)('field', 1)


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


class TestPathFragment(TypeTestCase):
    def test_valid(self):
        self.assertEqual(path_fragment('field', 'path'), 'path')
        self.assertEqual(path_fragment('field', 'path/..'), '.')
        self.assertEqual(path_fragment('field', 'foo/../bar'), 'bar')

    def test_outer(self):
        with self.assertFieldError(('field',)):
            path_fragment('field', '../path')
        with self.assertFieldError(('field',)):
            path_fragment('field', 'path/../..')

    def test_absolute_posix(self):
        with mock.patch('os.path', posixpath):
            with self.assertFieldError(('field',)):
                path_fragment('field', '/path')

    def test_absolute_nt(self):
        with mock.patch('os.path', ntpath):
            with self.assertFieldError(('field',)):
                path_fragment('field', '/path')
            with self.assertFieldError(('field',)):
                path_fragment('field', 'C:path')
            with self.assertFieldError(('field',)):
                path_fragment('field', 'C:\\path')
            with self.assertFieldError(('field',)):
                path_fragment('field', 'C:')


class TestAbsOrInnerPath(TypeTestCase):
    def test_inner(self):
        fn = abs_or_inner_path('cfgdir')
        self.assertEqual(fn('field', 'path'), Path('cfgdir', 'path'))
        self.assertEqual(fn('field', 'path/..'), Path('cfgdir', '.'))
        self.assertEqual(fn('field', 'foo/../bar'), Path('cfgdir', 'bar'))
        self.assertEqual(fn('field', Path('cfgdir', 'path')),
                         Path('cfgdir', 'path'))

    def test_outer(self):
        with self.assertFieldError(('field',)):
            abs_or_inner_path('cfgdir')('field', '../path')
        with self.assertFieldError(('field',)):
            abs_or_inner_path('cfgdir')('field', 'path/../..')

    def test_invalid_base(self):
        with self.assertFieldError(('field',)):
            abs_or_inner_path('cfgdir')('field', Path('srcdir', 'path'))

    def test_absolute_posix(self):
        with mock.patch('os.path', posixpath):
            self.assertEqual(abs_or_inner_path('cfgdir')('field', '/path'),
                             Path('absolute', '/path'))

    def test_absolute_nt(self):
        fn = abs_or_inner_path('cfgdir')
        with mock.patch('os.path', ntpath):
            self.assertEqual(fn('field', '/path'), Path('absolute', '\\path'))
            self.assertEqual(fn('field', 'C:\\path'),
                             Path('absolute', 'C:\\path'))
            with self.assertFieldError(('field',)):
                fn('field', 'C:')
            with self.assertFieldError(('field',)):
                fn('field', 'C:path')


class TestAnyPath(TypeTestCase):
    def test_relative(self):
        fn = any_path('cfgdir')
        self.assertEqual(fn('field', 'path'), Path('cfgdir', 'path'))
        self.assertEqual(fn('field', '../path'),
                         Path('cfgdir', os.path.join('..', 'path')))
        self.assertEqual(fn('field', 'foo/../bar'), Path('cfgdir', 'bar'))
        self.assertEqual(fn('field', Path('cfgdir', 'path')),
                         Path('cfgdir', 'path'))

    def test_absolute(self):
        fn = any_path('cfgdir')
        self.assertEqual(fn('field', '/path'),
                         Path('absolute', os.sep + 'path'))
        self.assertEqual(fn('field', '/path'),
                         Path('absolute', os.sep + 'path'))
        self.assertEqual(fn('field', Path('absolute', '/path')),
                         Path('absolute', '/path'))

    def test_invalid_base(self):
        with self.assertFieldError(('field',)):
            any_path('cfgdir')('field', Path('srcdir', 'path'))


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
    bases = ['srcdir', 'builddir']

    def assertShellArgs(self, value, expected, **kwargs):
        self.assertEqual(shell_args(self.bases, **kwargs)('field', value),
                         ShellArguments(expected))

    def test_none(self):
        self.assertShellArgs(None, [], none_ok=True)
        self.assertShellArgs(Unset, [], none_ok=True)

        with self.assertFieldError(('field',)):
            shell_args(self.bases)('field', None)
        with self.assertFieldError(('field',)):
            shell_args(self.bases)('field', Unset)

    def test_empty(self):
        self.assertShellArgs('', [])
        self.assertShellArgs([], [])

    def test_single(self):
        self.assertShellArgs('foo', ['foo'])

    def test_multiple(self):
        self.assertShellArgs('foo bar baz', ['foo', 'bar', 'baz'])

    def test_quote(self):
        self.assertShellArgs('foo "bar baz"', ['foo', 'bar baz'])
        self.assertShellArgs('foo"bar baz"', ['foobar baz'])

    def test_list(self):
        self.assertShellArgs(['foo', 'bar baz'], ['foo', 'bar baz'])

    def test_escapes(self):
        self.assertShellArgs('foo\\ bar', ['foo\\', 'bar'])
        self.assertShellArgs('foo\\ bar', ['foo bar'], escapes=True)

    def test_placeholder_string(self):
        srcdir = Path('srcdir', '')
        srcdir_ph = placeholder(srcdir)

        self.assertShellArgs(srcdir_ph, [srcdir])
        self.assertShellArgs(srcdir_ph + ' foo', [srcdir, 'foo'])
        self.assertShellArgs('foo ' + srcdir_ph + ' bar',
                             ['foo', srcdir, 'bar'])
        self.assertShellArgs(srcdir_ph + '/foo', [(srcdir, '/foo')])
        self.assertShellArgs('"' + srcdir_ph + '/ foo"',
                             [(srcdir, '/ foo')])

    def test_placeholder_list(self):
        srcdir = Path('srcdir', '')
        srcdir_ph = placeholder(srcdir)

        self.assertShellArgs([srcdir_ph], [srcdir])
        self.assertShellArgs(['foo', srcdir_ph, 'bar'],
                             ['foo', srcdir, 'bar'])
        self.assertShellArgs([srcdir_ph + '/foo'], [(srcdir, '/foo')])
        self.assertShellArgs([srcdir_ph + '/ foo'], [(srcdir, '/ foo')])

    def test_invalid(self):
        with self.assertFieldError(('field',)):
            shell_args(self.bases)('field', 1)
        with self.assertFieldError(('field', 0)):
            shell_args(self.bases)('field', [1])
        with self.assertFieldError(('field',)):
            shell_args(self.bases)('field', '"foo')


class TestWrapFieldError(TypeTestCase):
    def test_field_error(self):
        with self.assertFieldError(('outer', 'inner')):
            with wrap_field_error('outer'):
                raise FieldError('msg', 'inner')
        with self.assertFieldError(('outer', 'inner')):
            with wrap_field_error('outer', 'kind'):
                raise FieldError('msg', 'inner')

    def test_matching_type_error(self):
        msg = "foo got an unexpected keyword argument 'inner'"
        with self.assertRaises(TypeError):
            with wrap_field_error('outer'):
                raise TypeError(msg)
        with self.assertFieldError(('outer', 'inner')):
            with wrap_field_error('outer', 'kind'):
                raise TypeError(msg)

    def test_non_matching_type_error(self):
        with self.assertRaises(TypeError):
            with wrap_field_error('outer'):
                raise TypeError('msg')
        with self.assertRaises(TypeError):
            with wrap_field_error('outer', 'kind'):
                raise TypeError('msg')

    def test_other_error(self):
        with self.assertRaises(ValueError):
            with wrap_field_error('outer'):
                raise ValueError('msg')
        with self.assertRaises(ValueError):
            with wrap_field_error('outer', 'kind'):
                raise ValueError('msg')


class TestTryLoadConfig(TestCase):
    def load_data(self, data, Loader=SafeLineLoader):
        with mock.patch('builtins.open', mock.mock_open(read_data=data)):
            with load_file('file.yml', Loader=Loader) as f:
                return f

    def test_single_field(self):
        cfg = self.load_data('foo: Foo\nbar: Bar\n')
        with self.assertRaisesRegex(MarkedYAMLError,
                                    '^context\n' +
                                    '  in ".*", line 1, column 1\n' +
                                    'expected a boolean\n' +
                                    '  in ".*", line 1, column 6$'):
            with try_load_config(cfg, 'context', 'kind'):
                boolean('foo', cfg['foo'])

    def test_multiple_fields(self):
        cfg = self.load_data('foo:\n  bar: Bar\n')
        with self.assertRaisesRegex(MarkedYAMLError,
                                    '^context\n' +
                                    '  in ".*", line 1, column 1\n' +
                                    'expected a boolean\n' +
                                    '  in ".*", line 2, column 8$'):
            with try_load_config(cfg, 'context', 'kind'):
                dict_shape({'bar': boolean}, 'a bar dict')('foo', cfg['foo'])
