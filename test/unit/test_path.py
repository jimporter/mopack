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


class TestPath(TestCase):
    def test_construct(self):
        p = Path(Path.Base.cfgdir, 'foo')
        self.assertEqual(p.base, Path.Base.cfgdir)
        self.assertEqual(p.path, 'foo')
        self.assertEqual(p.is_abs(), False)
        self.assertEqual(p.is_inner(), True)

        p = Path('cfgdir', 'foo')
        self.assertEqual(p.base, Path.Base.cfgdir)
        self.assertEqual(p.path, 'foo')
        self.assertEqual(p.is_abs(), False)
        self.assertEqual(p.is_inner(), True)

        p = Path(Path.Base.cfgdir, 'foo/bar')
        self.assertEqual(p.base, Path.Base.cfgdir)
        self.assertEqual(p.path, os.path.join('foo', 'bar'))
        self.assertEqual(p.is_abs(), False)
        self.assertEqual(p.is_inner(), True)

        p = Path(Path.Base.cfgdir, '../bar')
        self.assertEqual(p.base, Path.Base.cfgdir)
        self.assertEqual(p.path, os.path.join('..', 'bar'))
        self.assertEqual(p.is_abs(), False)
        self.assertEqual(p.is_inner(), False)

        p = Path(Path.Base.cfgdir, 'foo/bar/../baz')
        self.assertEqual(p.base, Path.Base.cfgdir)
        self.assertEqual(p.path, os.path.join('foo', 'baz'))
        self.assertEqual(p.is_abs(), False)
        self.assertEqual(p.is_inner(), True)

        p = Path(Path.Base.cfgdir, '/foo')
        self.assertEqual(p.base, Path.Base.absolute)
        self.assertEqual(p.path, os.sep + 'foo')
        self.assertEqual(p.is_abs(), True)
        self.assertEqual(p.is_inner(), True)

        p = Path(Path.Base.absolute, '/foo')
        self.assertEqual(p.base, Path.Base.absolute)
        self.assertEqual(p.path, os.sep + 'foo')
        self.assertEqual(p.is_abs(), True)
        self.assertEqual(p.is_inner(), True)

        p = Path(None, '/foo')
        self.assertEqual(p.base, Path.Base.absolute)
        self.assertEqual(p.path, os.sep + 'foo')
        self.assertEqual(p.is_abs(), True)
        self.assertEqual(p.is_inner(), True)

        p = Path(Path.Base.cfgdir, '.')
        self.assertEqual(p.base, Path.Base.cfgdir)
        self.assertEqual(p.path, '')
        self.assertEqual(p.is_abs(), False)
        self.assertEqual(p.is_inner(), True)

        p = Path(Path.Base.cfgdir, '')
        self.assertEqual(p.base, Path.Base.cfgdir)
        self.assertEqual(p.path, '')
        self.assertEqual(p.is_abs(), False)
        self.assertEqual(p.is_inner(), True)

    def test_construct_invalid(self):
        with self.assertRaises(TypeError):
            Path(Path.Base.cfgdir, 1)
        with self.assertRaises(TypeError):
            Path('goofy', 'foo')
        with self.assertRaises(ValueError):
            Path(Path.Base.absolute, 'foo')
        with self.assertRaises(ValueError):
            Path(None, 'foo')

        with mock.patch('os.path', ntpath), \
             self.assertRaises(ValueError):  # noqa
            Path(Path.Base.cfgdir, 'C:foo')

    def test_ensure_path(self):
        self.assertEqual(Path.ensure_path('foo', Path.Base.srcdir),
                         Path(Path.Base.srcdir, 'foo'))
        self.assertEqual(Path.ensure_path(Path(Path.Base.srcdir, 'foo'),
                                          Path.Base.srcdir),
                         Path(Path.Base.srcdir, 'foo'))
        self.assertEqual(Path.ensure_path(Path(Path.Base.srcdir, 'foo'),
                                          Path.Base.builddir),
                         Path(Path.Base.srcdir, 'foo'))

    def test_ensure_path_placeholder(self):
        srcdir = placeholder(Path(Path.Base.srcdir, ''))
        self.assertEqual(Path.ensure_path(srcdir, Path.Base.srcdir),
                         Path(Path.Base.srcdir, ''))
        self.assertEqual(Path.ensure_path(srcdir + '/foo', Path.Base.srcdir),
                         Path(Path.Base.srcdir, 'foo'))

        subsrc = placeholder(Path(Path.Base.srcdir, 'subdir'))
        self.assertEqual(Path.ensure_path(subsrc, Path.Base.srcdir),
                         Path(Path.Base.srcdir, 'subdir'))
        self.assertEqual(Path.ensure_path(subsrc + '/foo', Path.Base.srcdir),
                         Path(Path.Base.srcdir, 'subdir/foo'))
        self.assertEqual(Path.ensure_path(subsrc + 'foo', Path.Base.srcdir),
                         Path(Path.Base.srcdir, 'subdirfoo'))

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

    def test_string(self):
        p = Path(Path.Base.srcdir, 'foo')
        self.assertEqual(p.string(srcdir='/srcdir'),
                         os.path.abspath(os.path.join('/srcdir', 'foo')))

        p = Path(Path.Base.absolute, '/foo')
        self.assertEqual(p.string(), os.path.abspath('/foo'))

    def test_rehydrate(self):
        p = Path(Path.Base.srcdir, 'foo')
        data = p.dehydrate()
        self.assertEqual(p, Path.rehydrate(data))

        with self.assertRaises(TypeError):
            Path.rehydrate('foo')
