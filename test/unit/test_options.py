from unittest import mock, TestCase

from . import through_json

from mopack.options import CommonOptions
from mopack.path import Path
from mopack.placeholder import placeholder


class TestCommonOptions(TestCase):
    def test_augment_symbols(self):
        opts = CommonOptions()
        opts.finalize()

        self.assertIs(opts.expr_symbols.augment(), opts.expr_symbols)
        self.assertEqual(
            opts.expr_symbols.augment(paths=['cfgdir']),
            {**opts.expr_symbols, 'cfgdir': placeholder(Path('', 'cfgdir'))}
        )
        self.assertEqual(
            opts.expr_symbols.augment(symbols={'foo': 'bar'}),
            {**opts.expr_symbols, 'foo': 'bar'}
        )

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
