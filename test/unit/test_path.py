import ntpath
import os
from unittest import mock, TestCase

from mopack.placeholder import placeholder
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
        p = Path('foo', Path.Base.cfgdir)
        self.assertEqual(p.base, Path.Base.cfgdir)
        self.assertEqual(p.path, 'foo')
        self.assertEqual(p.is_abs(), False)
        self.assertEqual(p.is_inner(), True)

        p = Path('foo', 'cfgdir')
        self.assertEqual(p.base, Path.Base.cfgdir)
        self.assertEqual(p.path, 'foo')
        self.assertEqual(p.is_abs(), False)
        self.assertEqual(p.is_inner(), True)

        p = Path('foo/bar', Path.Base.cfgdir)
        self.assertEqual(p.base, Path.Base.cfgdir)
        self.assertEqual(p.path, os.path.join('foo', 'bar'))
        self.assertEqual(p.is_abs(), False)
        self.assertEqual(p.is_inner(), True)

        p = Path('../bar', Path.Base.cfgdir)
        self.assertEqual(p.base, Path.Base.cfgdir)
        self.assertEqual(p.path, os.path.join('..', 'bar'))
        self.assertEqual(p.is_abs(), False)
        self.assertEqual(p.is_inner(), False)

        p = Path('foo/bar/../baz', Path.Base.cfgdir)
        self.assertEqual(p.base, Path.Base.cfgdir)
        self.assertEqual(p.path, os.path.join('foo', 'baz'))
        self.assertEqual(p.is_abs(), False)
        self.assertEqual(p.is_inner(), True)

        p = Path('/foo', Path.Base.cfgdir)
        self.assertEqual(p.base, Path.Base.absolute)
        self.assertEqual(p.path, os.sep + 'foo')
        self.assertEqual(p.is_abs(), True)
        self.assertEqual(p.is_inner(), True)

        p = Path('/foo', Path.Base.absolute)
        self.assertEqual(p.base, Path.Base.absolute)
        self.assertEqual(p.path, os.sep + 'foo')
        self.assertEqual(p.is_abs(), True)
        self.assertEqual(p.is_inner(), True)

        p = Path('/foo')
        self.assertEqual(p.base, Path.Base.absolute)
        self.assertEqual(p.path, os.sep + 'foo')
        self.assertEqual(p.is_abs(), True)
        self.assertEqual(p.is_inner(), True)

        p = Path('.', Path.Base.cfgdir)
        self.assertEqual(p.base, Path.Base.cfgdir)
        self.assertEqual(p.path, '')
        self.assertEqual(p.is_abs(), False)
        self.assertEqual(p.is_inner(), True)

        p = Path('', Path.Base.cfgdir)
        self.assertEqual(p.base, Path.Base.cfgdir)
        self.assertEqual(p.path, '')
        self.assertEqual(p.is_abs(), False)
        self.assertEqual(p.is_inner(), True)

    def test_construct_invalid(self):
        with self.assertRaises(TypeError):
            Path(1, Path.Base.cfgdir)
        with self.assertRaises(TypeError):
            Path('foo', 'goofy')
        with self.assertRaises(ValueError):
            Path('foo', Path.Base.absolute)

        with mock.patch('os.path', ntpath), \
             self.assertRaises(ValueError):
            Path('C:foo', Path.Base.cfgdir)

    def test_ensure_path(self):
        self.assertEqual(Path.ensure_path('foo', Path.Base.srcdir),
                         Path('foo', Path.Base.srcdir))
        self.assertEqual(Path.ensure_path(Path('foo', Path.Base.srcdir),
                                          Path.Base.srcdir),
                         Path('foo', Path.Base.srcdir))
        self.assertEqual(Path.ensure_path(Path('foo', Path.Base.srcdir),
                                          Path.Base.builddir),
                         Path('foo', Path.Base.srcdir))

    def test_ensure_path_placeholder(self):
        srcdir = placeholder(Path('', Path.Base.srcdir))
        self.assertEqual(Path.ensure_path(srcdir, Path.Base.srcdir),
                         Path('', Path.Base.srcdir))
        self.assertEqual(Path.ensure_path(srcdir + '/foo', Path.Base.srcdir),
                         Path('foo', Path.Base.srcdir))

        subsrc = placeholder(Path('subdir', Path.Base.srcdir))
        self.assertEqual(Path.ensure_path(subsrc, Path.Base.srcdir),
                         Path('subdir', Path.Base.srcdir))
        self.assertEqual(Path.ensure_path(subsrc + '/foo', Path.Base.srcdir),
                         Path('subdir/foo', Path.Base.srcdir))
        self.assertEqual(Path.ensure_path(subsrc + 'foo', Path.Base.srcdir),
                         Path('subdirfoo', Path.Base.srcdir))

        with self.assertRaises(ValueError):
            Path.ensure_path(srcdir + 'foo', Path.Base.srcdir)
        with self.assertRaises(ValueError):
            Path.ensure_path(srcdir + '/foo' + srcdir, Path.Base.srcdir)

    def test_base_filter(self):
        bases = ['srcdir', 'builddir']
        self.assertEqual(Path.Base.filter(bases, {}), [])
        self.assertEqual(Path.Base.filter(bases, {'srcdir', 'builddir'}),
                         [Path.Base.srcdir, Path.Base.builddir])
        self.assertEqual(Path.Base.filter(bases, {'srcdir'}),
                         [Path.Base.srcdir])
        self.assertEqual(Path.Base.filter(bases, {'cfgdir', 'srcdir'}),
                         [Path.Base.srcdir])

    def test_append(self):
        p = Path('foo', Path.Base.srcdir)
        self.assertEqual(p.append('bar'), Path('foo/bar', Path.Base.srcdir))
        self.assertEqual(p.append('../bar'), Path('bar', Path.Base.srcdir))
        self.assertEqual(p.append('..'), Path('', Path.Base.srcdir))
        self.assertEqual(p.append('/bar'), Path('/bar', Path.Base.absolute))

    def test_hash(self):
        d = {Path('.', Path.Base.srcdir),
             Path('.', Path.Base.builddir),
             Path('foo', Path.Base.srcdir)}
        self.assertEqual(len(d), 3)

    def test_string(self):
        p = Path('foo', Path.Base.srcdir)
        self.assertEqual(p.string(srcdir=('${srcdir}')),
                         os.path.join('${srcdir}', 'foo'))
        self.assertEqual(p.string(srcdir=os.path.abspath('/srcdir')),
                         os.path.abspath(os.path.join('/srcdir', 'foo')))

        p = Path('/foo')
        self.assertEqual(p.string(), os.path.abspath('/foo'))

    def test_rehydrate(self):
        p = Path('foo', Path.Base.srcdir)
        data = p.dehydrate()
        self.assertEqual(p, Path.rehydrate(data))

        with self.assertRaises(TypeError):
            Path.rehydrate('foo')
