import copy
import os
from unittest import mock, TestCase

from . import through_json

from mopack.options import *
from mopack.path import Path
from mopack.placeholder import placeholder
from mopack.platforms import platform_name


class TestExprSymbols(TestCase):
    def test_empty(self):
        symbols = ExprSymbols()
        self.assertEqual(symbols, {})
        self.assertEqual(symbols.path_bases, ())

    def test_augment_symbols(self):
        symbols = ExprSymbols(foo='bar')

        symbols = symbols.augment(symbols={'baz': 'quux'})
        self.assertEqual(symbols, {'foo': 'bar', 'baz': 'quux'})
        self.assertEqual(symbols.path_bases, ())

    def test_augment_path_bases(self):
        symbols = ExprSymbols(foo='bar')

        symbols = symbols.augment(path_bases=['cfgdir'])
        self.assertEqual(symbols, {
            'foo': 'bar',
            'cfgdir': placeholder(Path('', 'cfgdir')),
        })
        self.assertEqual(symbols.path_bases, ('cfgdir',))

        symbols = symbols.augment(path_bases=['srcdir'])
        self.assertEqual(symbols, {
            'foo': 'bar',
            'cfgdir': placeholder(Path('', 'cfgdir')),
            'srcdir': placeholder(Path('', 'srcdir')),
        })
        self.assertEqual(symbols.path_bases, ('cfgdir', 'srcdir'))

    def test_augment_duplicate(self):
        symbols = ExprSymbols(foo='bar')
        with self.assertRaises(DuplicateSymbolError):
            symbols.augment(symbols={'foo': 'baz'})
        with self.assertRaises(DuplicateSymbolError):
            symbols.augment(path_bases=['foo'])

    def test_best_path_base(self):
        symbols = ExprSymbols()
        self.assertEqual(symbols.best_path_base('srcdir'), None)

        symbols = symbols.augment(path_bases=['srcdir', 'builddir'])
        self.assertEqual(symbols.best_path_base('srcdir'), 'srcdir')
        self.assertEqual(symbols.best_path_base('builddir'), 'builddir')
        self.assertEqual(symbols.best_path_base('otherdir'), 'srcdir')

    def test_copy(self):
        symbols = ExprSymbols(foo='bar')

        symbols2 = symbols.copy()
        self.assertIsNot(symbols, symbols2)
        self.assertEqual(symbols, symbols2)
        self.assertEqual(symbols.path_bases, symbols2.path_bases)

        symbols2['baz'] = 'quux'
        self.assertNotEqual(symbols, symbols2)

        symbols3 = copy.copy(symbols)
        self.assertIsNot(symbols, symbols3)
        self.assertEqual(symbols, symbols3)
        self.assertEqual(symbols.path_bases, symbols3.path_bases)

    def test_deepcopy(self):
        symbols = ExprSymbols(foo='bar')

        symbols2 = copy.deepcopy(symbols)
        self.assertIsNot(symbols, symbols2)
        self.assertEqual(symbols, symbols2)
        self.assertEqual(symbols.path_bases, symbols2.path_bases)

        symbols2['baz'] = 'quux'
        self.assertNotEqual(symbols, symbols2)


class TestCommonOptions(TestCase):
    def test_default(self):
        opts = CommonOptions()
        opts.finalize()
        self.assertEqual(opts.strict, False)
        self.assertEqual(opts.target_platform, platform_name())
        self.assertEqual(opts.env, os.environ)
        self.assertEqual(opts.deploy_dirs, {})

    def test_strict(self):
        opts = CommonOptions()
        opts(strict=False)
        opts.finalize()
        self.assertEqual(opts.strict, False)

        opts = CommonOptions()
        opts(strict=True)
        opts.finalize()
        self.assertEqual(opts.strict, True)

        opts = CommonOptions()
        opts(strict=False)
        opts(strict=True)
        opts.finalize()
        self.assertEqual(opts.strict, False)

    def test_target_platform(self):
        opts = CommonOptions()
        opts(target_platform='linux')
        opts.finalize()
        self.assertEqual(opts.target_platform, 'linux')

        opts = CommonOptions()
        opts(target_platform='windows')
        opts.finalize()
        self.assertEqual(opts.target_platform, 'windows')

        opts = CommonOptions()
        opts(target_platform='linux')
        opts(target_platform='windows')
        opts.finalize()
        self.assertEqual(opts.target_platform, 'linux')

        opts = CommonOptions()
        opts(target_platform=None)
        opts(target_platform='goofy')
        opts.finalize()
        self.assertEqual(opts.target_platform, platform_name())

    def test_env(self):
        opts = CommonOptions()
        opts(env={'FOO': 'foo'})
        with mock.patch('os.environ', {'ENV': 'env'}):
            opts.finalize()
        self.assertEqual(opts.env, {'FOO': 'foo', 'ENV': 'env'})

        opts = CommonOptions()
        opts(env={'FOO': 'foo'})
        opts(env={'FOO': 'oof', 'BAR': 'bar'})
        with mock.patch('os.environ', {'ENV': 'env'}):
            opts.finalize()
        self.assertEqual(opts.env, {'FOO': 'foo', 'BAR': 'bar', 'ENV': 'env'})

    def test_variables(self):
        opts = CommonOptions()
        opts(env={'FOO': '$host_platform'})
        self.assertEqual(opts.env, {'FOO': platform_name()})

    def test_expr_symbols(self):
        opts = CommonOptions()
        opts.finalize()

        self.assertEqual(opts.expr_symbols, {
            'host_platform': platform_name(),
            'target_platform': platform_name(),
            'env': os.environ,
            'deploy_dirs': {},
        })

    def test_finalize(self):
        opts = CommonOptions()
        with self.assertRaises(RuntimeError):
            opts.expr_symbols
        opts.finalize()
        with self.assertRaises(RuntimeError):
            opts(env={'FOO': 'foo'})

    def test_rehydrate(self):
        opts = CommonOptions()
        opts(target_platform='linux', env={'VAR': 'value'})
        data = through_json(opts.dehydrate())
        self.assertEqual(opts, CommonOptions.rehydrate(data))

    def test_upgrade(self):
        data = {'_version': 0, 'target_platform': 'linux', 'env': {}}
        with mock.patch.object(CommonOptions, 'upgrade',
                               side_effect=CommonOptions.upgrade) as m:
            opts = CommonOptions.rehydrate(data)
            self.assertIsInstance(opts, CommonOptions)
            m.assert_called_once()
