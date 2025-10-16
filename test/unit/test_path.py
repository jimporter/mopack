import ntpath
import os
from unittest import mock, TestCase

from mopack.placeholder import PlaceholderString, placeholder
from mopack.path import *


class TestPushd(TestCase):
    def test_no_makedirs(self):
        with mock.patch('os.getcwd', return_value='dir'), \
             mock.patch('os.chdir') as mchdir, \
             mock.patch('os.makedirs') as mmakedirs, \
             pushd('foo'):
            pass

        self.assertEqual(mchdir.mock_calls, [mock.call('foo'),
                                             mock.call('dir')])
        mmakedirs.assert_not_called()

    def test_makedirs(self):
        with mock.patch('os.getcwd', return_value='dir'), \
             mock.patch('os.chdir') as mchdir, \
             mock.patch('os.makedirs') as mmakedirs, \
             pushd('foo', makedirs=True):
            pass

        self.assertEqual(mchdir.mock_calls, [mock.call('foo'),
                                             mock.call('dir')])
        mmakedirs.assert_called_once_with('foo', 0o777, False)


class TestFileOutdated(TestCase):
    def test_outdated(self):
        with mock.patch('os.path.getmtime', lambda p: 0 if p == 'foo' else 1):
            self.assertTrue(file_outdated('foo', 'bar'))

    def test_up_to_date(self):
        with mock.patch('os.path.getmtime', lambda p: 1 if p == 'foo' else 0):
            self.assertFalse(file_outdated('foo', 'bar'))

    def test_nonexist(self):
        def mock_getmtime(path):
            if path == 'bar':
                return 1
            raise FileNotFoundError()

        with mock.patch('os.path.getmtime', mock_getmtime):
            self.assertTrue(file_outdated('foo', 'bar'))

    def test_base_nonexist(self):
        with mock.patch('os.path.getmtime', side_effect=FileNotFoundError()):
            self.assertTrue(file_outdated('foo', 'bar'))
            self.assertFalse(file_outdated('foo', 'bar', False))


class TestPath(TestCase):
    def test_construct(self):
        p = Path('foo', 'cfgdir')
        self.assertEqual(p.base, 'cfgdir')
        self.assertEqual(p.path, 'foo')
        self.assertEqual(p.is_abs(), False)
        self.assertEqual(p.is_inner(), True)

        p = Path('foo', 'cfgdir')
        self.assertEqual(p.base, 'cfgdir')
        self.assertEqual(p.path, 'foo')
        self.assertEqual(p.is_abs(), False)
        self.assertEqual(p.is_inner(), True)

        p = Path('foo/bar', 'cfgdir')
        self.assertEqual(p.base, 'cfgdir')
        self.assertEqual(p.path, os.path.join('foo', 'bar'))
        self.assertEqual(p.is_abs(), False)
        self.assertEqual(p.is_inner(), True)

        p = Path('../bar', 'cfgdir')
        self.assertEqual(p.base, 'cfgdir')
        self.assertEqual(p.path, os.path.join('..', 'bar'))
        self.assertEqual(p.is_abs(), False)
        self.assertEqual(p.is_inner(), False)

        p = Path('foo/bar/../baz', 'cfgdir')
        self.assertEqual(p.base, 'cfgdir')
        self.assertEqual(p.path, os.path.join('foo', 'baz'))
        self.assertEqual(p.is_abs(), False)
        self.assertEqual(p.is_inner(), True)

        p = Path('/foo', 'cfgdir')
        self.assertEqual(p.base, None)
        self.assertEqual(p.path, os.sep + 'foo')
        self.assertEqual(p.is_abs(), True)
        self.assertEqual(p.is_inner(), True)

        p = Path('/foo', None)
        self.assertEqual(p.base, None)
        self.assertEqual(p.path, os.sep + 'foo')
        self.assertEqual(p.is_abs(), True)
        self.assertEqual(p.is_inner(), True)

        p = Path('/foo')
        self.assertEqual(p.base, None)
        self.assertEqual(p.path, os.sep + 'foo')
        self.assertEqual(p.is_abs(), True)
        self.assertEqual(p.is_inner(), True)

        p = Path('.', 'cfgdir')
        self.assertEqual(p.base, 'cfgdir')
        self.assertEqual(p.path, '')
        self.assertEqual(p.is_abs(), False)
        self.assertEqual(p.is_inner(), True)

        p = Path('', 'cfgdir')
        self.assertEqual(p.base, 'cfgdir')
        self.assertEqual(p.path, '')
        self.assertEqual(p.is_abs(), False)
        self.assertEqual(p.is_inner(), True)

    def test_construct_invalid(self):
        with self.assertRaises(TypeError):
            Path(1, 'cfgdir')
        with self.assertRaises(ValueError):
            Path('foo', 'goofy')
        with self.assertRaises(ValueError):
            Path('foo', None)

        with mock.patch('os.path', ntpath), \
             self.assertRaises(ValueError):
            Path('C:foo', 'cfgdir')

    def test_ensure_path(self):
        self.assertEqual(Path.ensure_path('foo', 'srcdir'),
                         Path('foo', 'srcdir'))
        self.assertEqual(Path.ensure_path(Path('foo', 'srcdir'),
                                          'srcdir'),
                         Path('foo', 'srcdir'))
        self.assertEqual(Path.ensure_path(Path('foo', 'srcdir'),
                                          'builddir'),
                         Path('foo', 'srcdir'))

    def test_ensure_path_placeholder(self):
        srcdir = placeholder(Path('', 'srcdir'))
        self.assertEqual(Path.ensure_path(srcdir, 'srcdir'),
                         Path('', 'srcdir'))
        self.assertEqual(Path.ensure_path(srcdir + '/foo', 'srcdir'),
                         Path('foo', 'srcdir'))

        subsrc = placeholder(Path('subdir', 'srcdir'))
        self.assertEqual(Path.ensure_path(subsrc, 'srcdir'),
                         Path('subdir', 'srcdir'))
        self.assertEqual(Path.ensure_path(subsrc + '/foo', 'srcdir'),
                         Path('subdir/foo', 'srcdir'))
        self.assertEqual(Path.ensure_path(subsrc + 'foo', 'srcdir'),
                         Path('subdirfoo', 'srcdir'))

        with self.assertRaises(ValueError):
            Path.ensure_path(srcdir + 'foo', 'srcdir')
        with self.assertRaises(ValueError):
            Path.ensure_path(srcdir + '/foo' + srcdir, 'srcdir')

    def test_append(self):
        p = Path('foo', 'srcdir')
        self.assertEqual(p.append('bar'), Path('foo/bar', 'srcdir'))
        self.assertEqual(p.append('../bar'), Path('bar', 'srcdir'))
        self.assertEqual(p.append('..'), Path('', 'srcdir'))
        self.assertEqual(p.append('/bar'), Path('/bar', None))

    def test_hash(self):
        d = {Path('.', 'srcdir'),
             Path('.', 'builddir'),
             Path('foo', 'srcdir')}
        self.assertEqual(len(d), 3)

    def test_string(self):
        p = Path('foo', 'srcdir')
        self.assertEqual(p.string({'srcdir': '${srcdir}'}),
                         os.path.join('${srcdir}', 'foo'))
        self.assertEqual(p.string({'srcdir': os.path.abspath('/srcdir')}),
                         os.path.abspath(os.path.join('/srcdir', 'foo')))

        p = Path('/foo')
        self.assertEqual(p.string(), os.path.abspath('/foo'))

    def test_rehydrate(self):
        p = Path('foo', 'srcdir')
        data = p.dehydrate()
        self.assertEqual(p, Path.rehydrate(data))

        with self.assertRaises(TypeError):
            Path.rehydrate('foo')

    def test_placeholder(self):
        p = Path('foo', 'srcdir')
        s = placeholder(p)
        data = s.dehydrate()
        self.assertEqual(s, PlaceholderString.rehydrate(data))
