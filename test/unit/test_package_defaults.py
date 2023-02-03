from unittest import mock, TestCase

from mopack.package_defaults import DefaultConfig, _get_default_config
from mopack.types import Unset
from mopack.yaml_tools import YamlParseError


def mock_open(read_data):
    return mock.mock_open(read_data=read_data)


class TestDefaultConfig(TestCase):
    def assertGet(self, cfg, args, expected, expected_raw=Unset):
        if expected_raw is Unset:
            expected_raw = expected
        self.assertEqual(cfg.get(*args), expected)
        self.assertEqual(cfg.get(*args, evaluate=False), expected_raw)

    def test_string_field(self):
        data = 'origin:\n  foo:\n    field: value'
        with mock.patch('builtins.open', mock_open(data)):
            cfg = DefaultConfig('file.yml')

        self.assertGet(cfg, ({}, 'origin', 'foo', 'field'), 'value')
        self.assertGet(cfg, ({}, 'origin', 'foo', 'other'), None)
        self.assertGet(cfg, ({}, 'origin', 'foo', 'other', 'default'),
                       'default')

        self.assertGet(cfg, ({}, 'origin', 'bar', 'field'), None)
        self.assertGet(cfg, ({}, 'origin', 'bar', 'field', 'default'),
                       'default')

        self.assertGet(cfg, ({}, 'usage', 'foo', 'field'), None)
        self.assertGet(cfg, ({}, 'usage', 'foo', 'field', 'default'),
                       'default')

    def test_list_field(self):
        data = 'origin:\n  foo:\n    field: [1, 2]'
        with mock.patch('builtins.open', mock_open(data)):
            cfg = DefaultConfig('file.yml')

        self.assertGet(cfg, ({}, 'origin', 'foo', 'field'), [1, 2])
        self.assertGet(cfg, ({}, 'origin', 'foo', 'other'), None)
        self.assertGet(cfg, ({}, 'origin', 'foo', 'other', []), [])
        self.assertGet(cfg, ({}, 'origin', 'bar', 'field'), None)
        self.assertGet(cfg, ({}, 'origin', 'bar', 'field', []), [])

    def test_dict_field(self):
        data = 'origin:\n  foo:\n    field: {goat: 1, panda: 2}'
        with mock.patch('builtins.open', mock_open(data)):
            cfg = DefaultConfig('file.yml')

        self.assertGet(cfg, ({}, 'origin', 'foo', 'field'),
                       {'goat': 1, 'panda': 2})
        self.assertGet(cfg, ({}, 'origin', 'foo', 'other'), None)
        self.assertGet(cfg, ({}, 'origin', 'foo', 'other', {}), {})
        self.assertGet(cfg, ({}, 'origin', 'bar', 'field'), None)
        self.assertGet(cfg, ({}, 'origin', 'bar', 'field', {}), {})

    def test_expr_field(self):
        data = 'origin:\n  foo:\n    field: $variable'
        with mock.patch('builtins.open', mock_open(data)):
            cfg = DefaultConfig('file.yml')

        symbols = {'variable': 'goat'}
        self.assertGet(cfg, (symbols, 'origin', 'foo', 'field'), 'goat',
                       '$variable')
        self.assertGet(cfg, (symbols, 'origin', 'bar', 'field'), None)

        symbols = {'variable': 'panda'}
        self.assertGet(cfg, (symbols, 'origin', 'foo', 'field'), 'panda',
                       '$variable')
        self.assertGet(cfg, (symbols, 'origin', 'bar', 'field'), None)

    def test_conditional(self):
        data = 'origin:\n  foo:\n    - if: true\n      field: goat'
        with mock.patch('builtins.open', mock_open(data)):
            cfg = DefaultConfig('file.yml')

        self.assertGet(cfg, ({}, 'origin', 'foo', 'field'), 'goat')
        self.assertGet(cfg, ({}, 'origin', 'bar', 'field'), None)

        data = 'origin:\n  foo:\n    - if: false\n      field: goat'
        with mock.patch('builtins.open', mock_open(data)):
            cfg = DefaultConfig('file.yml')

        self.assertGet(cfg, ({}, 'origin', 'foo', 'field'), None)
        self.assertGet(cfg, ({}, 'origin', 'bar', 'field'), None)

    def test_conditional_expr(self):
        data = ('origin:\n  foo:\n    - if: variable == true\n' +
                '      field: goat\n    - field: panda')
        with mock.patch('builtins.open', mock_open(data)):
            cfg = DefaultConfig('file.yml')

        symbols = {'variable': True}
        self.assertGet(cfg, (symbols, 'origin', 'foo', 'field'), 'goat')
        self.assertGet(cfg, (symbols, 'origin', 'bar', 'field'), None)

        symbols = {'variable': False}
        self.assertGet(cfg, (symbols, 'origin', 'foo', 'field'), 'panda')
        self.assertGet(cfg, (symbols, 'origin', 'bar', 'field'), None)

    def test_invalid_conditional(self):
        data = ('origin:\n  foo:\n    - field: goat\n    - field: panda')
        with mock.patch('builtins.open', mock_open(data)), \
             self.assertRaises(YamlParseError):
            DefaultConfig('file.yml')

    def test_invalid_genus(self):
        data = ('goofy:\n  foo:\n    field: value')
        with mock.patch('builtins.open', mock_open(data)), \
             self.assertRaises(YamlParseError):
            DefaultConfig('file.yml')

        data = ('origin:\n  foo:\n    field: value')
        with mock.patch('builtins.open', mock_open(data)):
            cfg = DefaultConfig('file.yml')
            with self.assertRaises(ValueError):
                cfg.get({}, 'goofy', 'foo', 'field')


class TestGetDefaultConfig(TestCase):
    def setUp(self):
        _get_default_config._reset()

    def tearDown(self):
        _get_default_config._reset()

    def test_normal(self):
        with mock.patch('os.path.exists', return_value=False) as mexists:
            _get_default_config('foo')
            mexists.assert_called_once()

    def test_invalid_characters(self):
        with mock.patch('os.path.exists', return_value=False) as mexists:
            _get_default_config('foo/bar')
            _get_default_config('.')
            _get_default_config('../foo')
            mexists.assert_not_called()
