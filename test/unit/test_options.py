import os
from unittest import mock, TestCase

from . import through_json

from mopack.options import CommonOptions
from mopack.path import Path
from mopack.placeholder import placeholder
from mopack.platforms import platform_name


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

    def test_augment_symbols(self):
        opts = CommonOptions()
        opts.finalize()

        symbols = opts.expr_symbols.augment_symbols(foo='bar')
        self.assertEqual(symbols, {**opts.expr_symbols, 'foo': 'bar'})
        self.assertEqual(symbols.path_bases, ())

    def test_augment_path_bases(self):
        opts = CommonOptions()
        opts.finalize()

        symbols = opts.expr_symbols.augment_path_bases('cfgdir')
        self.assertEqual(symbols, {
            **opts.expr_symbols, 'cfgdir': placeholder(Path('', 'cfgdir')),
        })
        self.assertEqual(symbols.path_bases, ('cfgdir',))

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
