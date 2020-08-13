import os.path
from unittest import mock, TestCase

from mopack.path import *


class TestTryJoin(TestCase):
    def test_second_absolute(self):
        self.assertEqual(try_join('/foo', '/bar'), os.path.abspath('/bar'))
        self.assertEqual(try_join(None, '/bar'), os.path.abspath('/bar'))

    def test_second_relative(self):
        self.assertEqual(try_join('/foo', 'bar'), os.path.abspath('/foo/bar'))
        self.assertRaises(TypeError, try_join, None, 'bar')


class TestPushd(TestCase):
    def test_no_makedirs(self):
        with mock.patch('os.getcwd', return_value='dir'), \
             mock.patch('os.chdir') as mchdir, \
             mock.patch('os.makedirs') as mmakedirs, \
             pushd('foo'):  # noqa
            pass

        self.assertEqual(mchdir.mock_calls, [mock.call('foo'),
                                             mock.call('dir')])
        mmakedirs.assert_not_called()

    def test_makedirs(self):
        with mock.patch('os.getcwd', return_value='dir'), \
             mock.patch('os.chdir') as mchdir, \
             mock.patch('os.makedirs') as mmakedirs, \
             pushd('foo', makedirs=True):  # noqa
            pass

        self.assertEqual(mchdir.mock_calls, [mock.call('foo'),
                                             mock.call('dir')])
        mmakedirs.assert_called_once_with('foo', 0o777, False)


class TestFilterGlob(TestCase):
    _common_paths = ['foo', 'foo/', 'foo/bar', 'foobar', 'bar', 'bar/',
                     'bar/foo', 'bar/foo/', 'bar/foo/baz', 'bar/baz/foo',
                     'baz/bar/foo']

    def _glob(self, pattern, paths=None, **kwargs):
        return list(filter_glob(pattern, paths or self._common_paths,
                                **kwargs))

    def test_absolute_simple(self):
        self.assertEqual(self._glob('/foo'), ['foo', 'foo/', 'foo/bar'])
        self.assertEqual(self._glob('/foo', match_child=False),
                         ['foo', 'foo/'])

        self.assertEqual(self._glob('/foo/'), ['foo/', 'foo/bar'])
        self.assertEqual(self._glob('/foo/', match_child=False), ['foo/'])

    def test_relative_simple(self):
        self.assertEqual(self._glob('foo'),
                         ['foo', 'foo/', 'foo/bar', 'bar/foo', 'bar/foo/',
                          'bar/foo/baz', 'bar/baz/foo', 'baz/bar/foo'])
        self.assertEqual(self._glob('foo', match_child=False),
                         ['foo', 'foo/', 'bar/foo', 'bar/foo/', 'bar/baz/foo',
                          'baz/bar/foo'])

        self.assertEqual(self._glob('foo/'),
                         ['foo/', 'foo/bar', 'bar/foo/', 'bar/foo/baz'])
        self.assertEqual(self._glob('foo/', match_child=False),
                         ['foo/', 'bar/foo/'])

    def test_absolute_multi(self):
        self.assertEqual(self._glob('/bar/foo'),
                         ['bar/foo', 'bar/foo/', 'bar/foo/baz'])
        self.assertEqual(self._glob('/bar/foo', match_child=False),
                         ['bar/foo', 'bar/foo/'])

        self.assertEqual(self._glob('/bar/foo/'), ['bar/foo/', 'bar/foo/baz'])
        self.assertEqual(self._glob('/bar/foo/', match_child=False),
                         ['bar/foo/'])

    def test_relative_multi(self):
        self.assertEqual(self._glob('bar/foo'),
                         ['bar/foo', 'bar/foo/', 'bar/foo/baz', 'baz/bar/foo'])
        self.assertEqual(self._glob('bar/foo', match_child=False),
                         ['bar/foo', 'bar/foo/', 'baz/bar/foo'])

        self.assertEqual(self._glob('bar/foo/'), ['bar/foo/', 'bar/foo/baz'])
        self.assertEqual(self._glob('bar/foo/', match_child=False),
                         ['bar/foo/'])

    def test_absolute_glob(self):
        self.assertEqual(self._glob('/ba*'),
                         ['bar', 'bar/', 'bar/foo', 'bar/foo/', 'bar/foo/baz',
                          'bar/baz/foo', 'baz/bar/foo'])
        self.assertEqual(self._glob('/ba*', match_child=False),
                         ['bar', 'bar/'])

        self.assertEqual(self._glob('/ba*/'),
                         ['bar/', 'bar/foo', 'bar/foo/', 'bar/foo/baz',
                          'bar/baz/foo', 'baz/bar/foo'])
        self.assertEqual(self._glob('/ba*/', match_child=False), ['bar/'])

        self.assertEqual(self._glob('/*ar'),
                         ['foobar', 'bar', 'bar/', 'bar/foo', 'bar/foo/',
                          'bar/foo/baz', 'bar/baz/foo'])
        self.assertEqual(self._glob('/*ar', match_child=False),
                         ['foobar', 'bar', 'bar/'])

        self.assertEqual(self._glob('/*ar/'),
                         ['bar/', 'bar/foo', 'bar/foo/', 'bar/foo/baz',
                          'bar/baz/foo'])
        self.assertEqual(self._glob('/*ar/', match_child=False), ['bar/'])

    def test_relative_glob(self):
        self.assertEqual(self._glob('ba*'),
                         ['foo/bar', 'bar', 'bar/', 'bar/foo', 'bar/foo/',
                          'bar/foo/baz', 'bar/baz/foo', 'baz/bar/foo'])
        self.assertEqual(self._glob('ba*', match_child=False),
                         ['foo/bar', 'bar', 'bar/'])

        self.assertEqual(self._glob('ba*/'),
                         ['bar/', 'bar/foo', 'bar/foo/', 'bar/foo/baz',
                          'bar/baz/foo', 'baz/bar/foo'])
        self.assertEqual(self._glob('ba*/', match_child=False), ['bar/'])

        self.assertEqual(self._glob('*ar'), [
            'foo/bar', 'foobar', 'bar', 'bar/', 'bar/foo', 'bar/foo/',
            'bar/foo/baz', 'bar/baz/foo', 'baz/bar/foo'
        ])
        self.assertEqual(self._glob('*ar', match_child=False),
                         ['foo/bar', 'foobar', 'bar', 'bar/'])

        self.assertEqual(self._glob('*ar/'),
                         ['bar/', 'bar/foo', 'bar/foo/', 'bar/foo/baz',
                          'bar/baz/foo', 'baz/bar/foo'])
        self.assertEqual(self._glob('*ar/', match_child=False), ['bar/'])

    def test_relative_starstar(self):
        self.assertEqual(self._glob('bar/**/foo'),
                         ['bar/foo', 'bar/foo/', 'bar/foo/baz', 'bar/baz/foo',
                          'baz/bar/foo'])
        self.assertEqual(self._glob('bar/**/foo', match_child=False),
                         ['bar/foo', 'bar/foo/', 'bar/baz/foo', 'baz/bar/foo'])

        self.assertEqual(self._glob('bar/**/foo/'),
                         ['bar/foo/', 'bar/foo/baz'])
        self.assertEqual(self._glob('bar/**/foo/', match_child=False),
                         ['bar/foo/'])

    def test_consecutive_starstar(self):
        self.assertEqual(self._glob('bar/**/**/foo'),
                         ['bar/foo', 'bar/foo/', 'bar/foo/baz', 'bar/baz/foo',
                          'baz/bar/foo'])
        self.assertEqual(self._glob('bar/**/**/foo', match_child=False),
                         ['bar/foo', 'bar/foo/', 'bar/baz/foo', 'baz/bar/foo'])

        self.assertEqual(self._glob('bar/**/**/foo/'),
                         ['bar/foo/', 'bar/foo/baz'])
        self.assertEqual(self._glob('bar/**/**/foo/', match_child=False),
                         ['bar/foo/'])

    def test_absolute_starstar_start(self):
        self.assertEqual(self._glob('/**/foo'),
                         ['foo', 'foo/', 'foo/bar', 'bar/foo', 'bar/foo/',
                          'bar/foo/baz', 'bar/baz/foo', 'baz/bar/foo'])
        self.assertEqual(self._glob('/**/foo', match_child=False),
                         ['foo', 'foo/', 'bar/foo', 'bar/foo/', 'bar/baz/foo',
                          'baz/bar/foo'])

        self.assertEqual(self._glob('/**/foo/'),
                         ['foo/', 'foo/bar', 'bar/foo/', 'bar/foo/baz'])
        self.assertEqual(self._glob('/**/foo/', match_child=False),
                         ['foo/', 'bar/foo/'])

    def test_relative_starstar_start(self):
        self.assertEqual(self._glob('**/foo'),
                         ['foo', 'foo/', 'foo/bar', 'bar/foo', 'bar/foo/',
                          'bar/foo/baz', 'bar/baz/foo', 'baz/bar/foo'])
        self.assertEqual(self._glob('**/foo', match_child=False),
                         ['foo', 'foo/', 'bar/foo', 'bar/foo/', 'bar/baz/foo',
                          'baz/bar/foo'])

        self.assertEqual(self._glob('**/foo/'),
                         ['foo/', 'foo/bar', 'bar/foo/', 'bar/foo/baz'])
        self.assertEqual(self._glob('**/foo/', match_child=False),
                         ['foo/', 'bar/foo/'])

    def test_starstar_end(self):
        self.assertEqual(self._glob('foo/**'),
                         ['foo/', 'foo/bar', 'bar/foo/', 'bar/foo/baz'])
        self.assertEqual(self._glob('foo/**', match_child=False),
                         ['foo/', 'foo/bar', 'bar/foo/', 'bar/foo/baz'])

        self.assertEqual(self._glob('foo/**/'),
                         ['foo/', 'foo/bar', 'bar/foo/', 'bar/foo/baz'])
        self.assertEqual(self._glob('foo/**/', match_child=False),
                         ['foo/', 'foo/bar', 'bar/foo/', 'bar/foo/baz'])

    def test_multiple(self):
        self.assertEqual(self._glob(['/foo', '/bar']),
                         ['foo', 'foo/', 'foo/bar', 'bar', 'bar/', 'bar/foo',
                          'bar/foo/', 'bar/foo/baz', 'bar/baz/foo'])
        self.assertEqual(self._glob(['/foo', '/bar'], match_child=False),
                         ['foo', 'foo/', 'bar', 'bar/'])

        self.assertEqual(self._glob(['/foo/', '/bar/']),
                         ['foo/', 'foo/bar', 'bar/', 'bar/foo', 'bar/foo/',
                          'bar/foo/baz', 'bar/baz/foo'])
        self.assertEqual(self._glob(['/foo/', '/bar/'], match_child=False),
                         ['foo/', 'bar/'])

    def test_empty(self):
        self.assertEqual(self._glob(''), self._common_paths)
        self.assertEqual(self._glob('', match_child=False), [])

        self.assertEqual(self._glob('/'), self._common_paths)
        self.assertEqual(self._glob('/', match_child=False), [])

    def test_explicit_glob(self):
        g = Glob('/foo')
        self.assertEqual(self._glob(g), ['foo', 'foo/', 'foo/bar'])
        self.assertEqual(self._glob(g, match_child=False), ['foo', 'foo/'])
