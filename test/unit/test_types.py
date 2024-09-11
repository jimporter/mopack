import ntpath
import os
import posixpath
from contextlib import contextmanager
from unittest import mock, TestCase

from . import mock_open_data

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


class TestUnset(TestCase):
    def test_bool(self):
        self.assertFalse(bool(Unset))

    def test_eq(self):
        self.assertTrue(Unset == Unset)
        self.assertTrue(Unset == None)  # noqa: E711
        self.assertFalse(Unset == 0)
        self.assertFalse(Unset == '')

        self.assertFalse(Unset != Unset)
        self.assertFalse(Unset != None)  # noqa: E711
        self.assertTrue(Unset != 0)
        self.assertTrue(Unset != '')

    def test_dehydrate(self):
        self.assertEqual(Unset.dehydrate(), None)
        self.assertEqual(type(Unset).rehydrate(None), Unset)
        with self.assertRaises(ValueError):
            type(Unset).rehydrate(0)


class TestTypeCheck(TypeTestCase):
    def test_object(self):
        class Thing:
            def __init__(self, field):
                T = TypeCheck(locals(), {})
                T.field(string)

        self.assertEqual(Thing('foo').field, 'foo')
        with self.assertFieldError(('field',)):
            Thing(1)

    def test_dest(self):
        class Thing:
            pass

        thing = Thing()
        field = 'foo'
        T = TypeCheck(locals(), dest=thing)
        T.field(string)

        self.assertEqual(thing.field, 'foo')

    def test_dest_dict(self):
        thing = {}
        field = 'foo'
        T = TypeCheck(locals(), dest=thing)
        T.field(string)

        self.assertEqual(thing['field'], 'foo')

    def test_dest_field(self):
        class Thing:
            def __init__(self, field):
                T = TypeCheck(locals(), {})
                T.field(string, dest_field='dest')

        self.assertEqual(Thing('foo').dest, 'foo')

    def test_per_field_dest_dict(self):
        class Thing:
            def __init__(self, field):
                self.data = {}
                T = TypeCheck(locals())
                T.field(string, dest=self.data)

        self.assertEqual(Thing('foo').data['field'], 'foo')
        with self.assertFieldError(('field',)):
            Thing(1)

    def test_object_reducer(self):
        class Thing:
            def __init__(self):
                self.field = []

            def __call__(self, field):
                T = TypeCheck(locals())
                T.field(list_of(string, listify=True),
                        reducer=lambda a, b: a + b)

        t = Thing()
        t('foo')
        t(['bar', 'baz'])
        self.assertEqual(t.field, ['foo', 'bar', 'baz'])
        with self.assertFieldError(('field',)):
            t(1)

    def test_dict_reducer(self):
        class Thing:
            def __init__(self):
                self.data = {'field': []}

            def __call__(self, field):
                T = TypeCheck(locals())
                T.field(list_of(string, listify=True), dest=self.data,
                        reducer=lambda a, b: a + b)

        t = Thing()
        t('foo')
        t(['bar', 'baz'])
        self.assertEqual(t.data['field'], ['foo', 'bar', 'baz'])
        with self.assertFieldError(('field',)):
            t(1)

    def test_evaluate(self):
        symbols = {'variable': 'value', 'bad': 1}

        class Thing:
            def __init__(self, field):
                T = TypeCheck(locals(), symbols)
                T.field(string)

        self.assertEqual(Thing('$variable').field, 'value')
        with self.assertFieldError(('field',)):
            Thing('$bad')
        with self.assertFieldError(('field',)):
            Thing('$undef')

    def test_evaluate_list(self):
        symbols = {'variable': 'value', 'bad': 1}

        class Thing:
            def __init__(self, field):
                T = TypeCheck(locals(), symbols)
                T.field(list_of(string))

        self.assertEqual(Thing(['foo', '$variable']).field, ['foo', 'value'])
        with self.assertFieldError(('field', 0)):
            Thing(['$bad'])
        with self.assertFieldError(('field', 0)):
            Thing(['$undef'])

    def test_evaluate_dict(self):
        symbols = {'variable': 'value', 'bad': 1}

        class Thing:
            def __init__(self, field):
                T = TypeCheck(locals(), symbols)
                T.field(dict_of(string, string))

        self.assertEqual(Thing({'foo': '$variable'}).field, {'foo': 'value'})
        with self.assertFieldError(('field', 'foo')):
            Thing({'foo': '$bad'})
        with self.assertFieldError(('field', 'foo')):
            Thing({'foo': '$undef'})

    def test_evaluate_extra_symbols(self):
        symbols = {'variable': 'value', 'bad': 1}

        class Thing:
            def __init__(self, field):
                T = TypeCheck(locals(), symbols)
                T.field(string, extra_symbols={'extra': 'goat'})

        self.assertEqual(Thing('$variable').field, 'value')
        self.assertEqual(Thing('$extra').field, 'goat')

        class ThingNoSymbols:
            def __init__(self, field):
                T = TypeCheck(locals())
                T.field(string, extra_symbols={'extra': 'goat'})

        self.assertEqual(ThingNoSymbols('$extra').field, 'goat')

    def test_no_evaluate(self):
        class Thing:
            def __init__(self, field):
                T = TypeCheck(locals())
                T.field(string)

        self.assertEqual(Thing('foo').field, 'foo')
        self.assertEqual(Thing('$variable').field, '$variable')

    def test_no_evaluate_override(self):
        symbols = {'variable': 'value', 'bad': 1}

        class Thing:
            def __init__(self, field, field2):
                T = TypeCheck(locals(), symbols)
                T.field(string)
                T.field2(string, evaluate=False)

        t = Thing('$variable', '$variable')
        self.assertEqual(t.field, 'value')
        self.assertEqual(t.field2, '$variable')

    def test_preserve_originals(self):
        symbols = {'variable': 'value'}

        class Thing:
            def __init__(self, field):
                T = TypeCheck(locals(), symbols)
                T.field(list_of(string))

        data = ['$variable']
        self.assertEqual(Thing(data).field, ['value'])
        self.assertEqual(data, ['$variable'])


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
        with self.assertFieldError(('field',), 'expected a non-empty list'):
            list_of(string, allow_empty=False)('field', [])
        with self.assertFieldError(('field',), 'expected a non-empty list'):
            list_of(string, listify=True, allow_empty=False)('field', None)
        with self.assertFieldError(('field', 0), 'expected a string'):
            list_of(string)('field', [1])
        with self.assertFieldError(('field',), 'expected a string'):
            list_of(string, listify=True)('field', 1)


class TestListOfLength(TypeTestCase):
    def test_list(self):
        self.assertEqual(list_of_length(string, 0)('field', []), [])
        self.assertEqual(list_of_length(string, 1)('field', ['foo']), ['foo'])
        self.assertEqual(list_of_length(string, 2)('field', ['foo', 'bar']),
                         ['foo', 'bar'])

    def test_invalid(self):
        with self.assertFieldError(('field',), 'expected a list'):
            list_of_length(string, 2)('field', None)
        with self.assertFieldError(('field',), 'expected a list'):
            list_of_length(string, 2)('field', 'foo')
        with self.assertFieldError(('field',), 'expected a list'):
            list_of_length(string, 2)('field', {})
        with self.assertFieldError(('field',), 'expected a list of length 2'):
            list_of_length(string, 2)('field', ['foo'])
        with self.assertFieldError(('field', 0), 'expected a string'):
            list_of_length(string, 2)('field', [1, 2])


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
            dict_of(string, boolean)('field', {'f': 'foo'})


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
        with self.assertFieldError(('field',)):
            string('field', placeholder('foo'))


class TestPlaceholderString(TypeTestCase):
    def test_valid(self):
        s = placeholder('foo')
        self.assertEqual(placeholder_string('field', 'foo'), 'foo')
        self.assertEqual(placeholder_string('field', s), s)

    def test_invalid(self):
        with self.assertFieldError(('field',)):
            placeholder_string('field', 1)
        with self.assertFieldError(('field',)):
            placeholder_string('field', None)


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
        self.assertEqual(path_fragment('field', 'path/sub'),
                         os.path.join('path', 'sub'))
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

    def test_invalid(self):
        with self.assertFieldError(('field',)):
            path_fragment('field', 1)
        with self.assertFieldError(('field',)):
            path_fragment('field', None)


class TestPathString(TypeTestCase):
    def test_valid(self):
        self.assertEqual(path_string('/base')('field', 'path'),
                         os.path.join(os.sep, 'base', 'path'))
        self.assertEqual(path_string('/base')('field', 'path/sub'),
                         os.path.join(os.sep, 'base', 'path', 'sub'))
        self.assertEqual(path_string('/base')('field', '../path'),
                         os.path.join(os.sep, 'path'))

    def test_invalid(self):
        with self.assertFieldError(('field',)):
            path_string('/base')('field', 1)
        with self.assertFieldError(('field',)):
            path_string('/base')('field', None)


class TestAbsOrInnerPath(TypeTestCase):
    def test_inner(self):
        fn = abs_or_inner_path('cfgdir')
        self.assertEqual(fn('field', 'path'), Path('path', 'cfgdir'))
        self.assertEqual(fn('field', 'path/..'), Path('.', 'cfgdir'))
        self.assertEqual(fn('field', 'foo/../bar'), Path('bar', 'cfgdir'))
        self.assertEqual(fn('field', Path('path', 'cfgdir')),
                         Path('path', 'cfgdir'))

    def test_outer(self):
        with self.assertFieldError(('field',)):
            abs_or_inner_path('cfgdir')('field', '../path')
        with self.assertFieldError(('field',)):
            abs_or_inner_path('cfgdir')('field', 'path/../..')

    def test_other_base(self):
        self.assertEqual(
            abs_or_inner_path('cfgdir')('field', Path('path', 'srcdir')),
            Path('path', 'srcdir')
        )

    def test_absolute_posix(self):
        with mock.patch('os.path', posixpath):
            for i in ('cfgdir', None):
                self.assertEqual(abs_or_inner_path(i)('field', '/path'),
                                 Path('/path'))

    def test_absolute_nt(self):
        fn = abs_or_inner_path('cfgdir')
        with mock.patch('os.path', ntpath):
            for i in ('cfgdir', None):
                fn = abs_or_inner_path('cfgdir')
                self.assertEqual(fn('field', '/path'), Path('\\path'))
                self.assertEqual(fn('field', 'C:\\path'), Path('C:\\path'))
                with self.assertFieldError(('field',)):
                    fn('field', 'C:')
                with self.assertFieldError(('field',)):
                    fn('field', 'C:path')


class TestAnyPath(TypeTestCase):
    def test_relative(self):
        fn = any_path('cfgdir')
        self.assertEqual(fn('field', 'path'), Path('path', 'cfgdir'))
        self.assertEqual(fn('field', '../path'),
                         Path(os.path.join('..', 'path'), 'cfgdir'))
        self.assertEqual(fn('field', 'foo/../bar'), Path('bar', 'cfgdir'))
        self.assertEqual(fn('field', Path('path', 'cfgdir')),
                         Path('path', 'cfgdir'))

    def test_absolute(self):
        for i in ('cfgdir', None):
            fn = any_path('cfgdir')
            self.assertEqual(fn('field', '/path'), Path(os.sep + 'path'))
            self.assertEqual(fn('field', '/path'), Path(os.sep + 'path'))
            self.assertEqual(fn('field', Path('/path')), Path('/path'))

    def test_other_base(self):
        self.assertEqual(any_path('cfgdir')('field', Path('path', 'srcdir')),
                         Path('path', 'srcdir'))


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


class TestDependency(TypeTestCase):
    def test_package(self):
        self.assertEqual(dependency('field', 'package'), ('package', None))
        self.assertEqual(dependency('field', 'red-panda'), ('red-panda', None))

    def test_submodules(self):
        self.assertEqual(dependency('field', 'pkg[sub]'), ('pkg', ['sub']))
        self.assertEqual(dependency('field', 'pkg[foo,bar]'),
                         ('pkg', ['foo', 'bar']))

    def test_invalid(self):
        not_deps = ['pkg,',
                    'pkg[',
                    'pkg]',
                    'pkg[]',
                    'pkg[sub,]',
                    'pkg[,sub]']
        for i in not_deps:
            with self.assertFieldError(('field',)):
                dependency('field', i)

    def test_dependency_string(self):
        self.assertEqual(dependency_string('pkg', None), 'pkg')
        self.assertEqual(dependency_string('pkg', []), 'pkg')
        self.assertEqual(dependency_string('pkg', 'foo'), 'pkg[foo]')
        self.assertEqual(dependency_string('pkg', ['foo']), 'pkg[foo]')
        self.assertEqual(dependency_string('pkg', ['foo', 'bar']),
                         'pkg[foo,bar]')
        self.assertEqual(dependency_string('pkg', iter(['foo', 'bar'])),
                         'pkg[foo,bar]')

    def test_invalid_dependency_string(self):
        not_deps = [('pkg,', None),
                    ('pkg[', None),
                    ('pkg]', None),
                    ('pkg', ['foo,']),
                    ('pkg', ['foo[']),
                    ('pkg', ['foo]']),
                    ('pkg', ['foo', 'bar['])]
        for i in not_deps:
            with self.assertRaises(ValueError):
                dependency_string(*i)


class TestShellArgs(TypeTestCase):
    def assertShellArgs(self, value, expected, **kwargs):
        self.assertEqual(shell_args(**kwargs)('field', value),
                         ShellArguments(expected))

    def test_none(self):
        self.assertShellArgs(None, [], none_ok=True)
        self.assertShellArgs(Unset, [], none_ok=True)

        with self.assertFieldError(('field',)):
            shell_args()('field', None)
        with self.assertFieldError(('field',)):
            shell_args()('field', Unset)

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
        srcdir = Path('', 'srcdir')
        srcdir_ph = placeholder(srcdir)

        self.assertShellArgs(srcdir_ph, [srcdir])
        self.assertShellArgs(srcdir_ph + ' foo', [srcdir, 'foo'])
        self.assertShellArgs('foo ' + srcdir_ph + ' bar',
                             ['foo', srcdir, 'bar'])
        self.assertShellArgs(srcdir_ph + '/foo', [(srcdir, '/foo')])
        self.assertShellArgs('"' + srcdir_ph + '/ foo"',
                             [(srcdir, '/ foo')])

    def test_placeholder_list(self):
        srcdir = Path('', 'srcdir')
        srcdir_ph = placeholder(srcdir)

        self.assertShellArgs([srcdir_ph], [srcdir])
        self.assertShellArgs(['foo', srcdir_ph, 'bar'],
                             ['foo', srcdir, 'bar'])
        self.assertShellArgs([srcdir_ph + '/foo'], [(srcdir, '/foo')])
        self.assertShellArgs([srcdir_ph + '/ foo'], [(srcdir, '/ foo')])

    def test_invalid(self):
        with self.assertFieldError(('field',)):
            shell_args()('field', 1)
        with self.assertFieldError(('field', 0)):
            shell_args()('field', [1])
        with self.assertFieldError(('field',)):
            shell_args()('field', '"foo')


class TestPlaceholderFill(TypeTestCase):
    p = placeholder(1)

    def test_foo(self):
        check = placeholder_fill(string, 1, 'one')
        self.assertEqual(check('field', 'foo'), 'foo')
        self.assertEqual(check('field', self.p), 'one')
        self.assertEqual(check('field', 'foo' + self.p), 'fooone')

    def test_dict(self):
        check = placeholder_fill(dict_shape({'foo': string}, 'a foo dict'), 1,
                                 'one')
        self.assertEqual(check('field', {'foo': 'bar'}), {'foo': 'bar'})
        self.assertEqual(check('field', {'foo': self.p}), {'foo': 'one'})
        self.assertEqual(check('field', {'foo': 'bar' + self.p}),
                         {'foo': 'barone'})

        with self.assertFieldError(('field', 'bad'), 'unexpected key'):
            check('field', {'bad': self.p})

    def test_invalid_type(self):
        with self.assertFieldError(('field',), 'expected a boolean'):
            placeholder_fill(boolean, 1, 'one')('field', self.p)


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
        with self.assertRaises(TypeError) as e:
            with wrap_field_error('outer'):
                raise TypeError(msg)
        self.assertNotIsInstance(e.exception, FieldError)
        with self.assertFieldError(('outer', 'inner')):
            with wrap_field_error('outer', 'kind'):
                raise TypeError(msg)

    def test_non_matching_type_error(self):
        with self.assertRaises(TypeError) as e:
            with wrap_field_error('outer'):
                raise TypeError('msg')
        self.assertNotIsInstance(e.exception, FieldError)
        with self.assertRaises(TypeError) as e:
            with wrap_field_error('outer', 'kind'):
                raise TypeError('msg')
        self.assertNotIsInstance(e.exception, FieldError)

    def test_other_error(self):
        with self.assertRaises(ValueError) as e:
            with wrap_field_error('outer'):
                raise ValueError('msg')
        self.assertNotIsInstance(e.exception, FieldError)
        with self.assertRaises(ValueError) as e:
            with wrap_field_error('outer', 'kind'):
                raise ValueError('msg')
        self.assertNotIsInstance(e.exception, FieldError)


class TestTryLoadConfig(TestCase):
    def load_data(self, data, Loader=SafeLineLoader):
        with mock.patch('builtins.open', mock_open_data(data)):
            with load_file('file.yml', Loader=Loader) as f:
                return f

    def test_single_field(self):
        cfg = self.load_data('foo: Foo\nbar: Bar\n')
        with self.assertRaisesRegex(MarkedYAMLOffsetError,
                                    '^context\n' +
                                    '  in ".*", line 1, column 1\n' +
                                    'expected a boolean\n' +
                                    '  in ".*", line 1, column 6$'):
            with try_load_config(cfg, 'context', 'kind'):
                boolean('foo', cfg['foo'])

    def test_multiple_fields(self):
        cfg = self.load_data('foo:\n  bar: Bar\n')
        with self.assertRaisesRegex(MarkedYAMLOffsetError,
                                    '^context\n' +
                                    '  in ".*", line 1, column 1\n' +
                                    'expected a boolean\n' +
                                    '  in ".*", line 2, column 8$'):
            with try_load_config(cfg, 'context', 'kind'):
                dict_shape({'bar': boolean}, 'a bar dict')('foo', cfg['foo'])
