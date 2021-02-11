from unittest import mock, TestCase

from . import through_json

from mopack.options import CommonOptions


class TestCommonOptions(TestCase):
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
