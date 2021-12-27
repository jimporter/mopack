from unittest import mock, TestCase

from mopack.package_defaults import DefaultConfig, _get_default_config
from mopack.yaml_tools import YamlParseError


def mock_open(read_data):
    return mock.mock_open(read_data=read_data)


class TestDefaultConfig(TestCase):
    def test_string_field(self):
        data = 'source:\n  foo:\n    field: value'
        with mock.patch('builtins.open', mock_open(data)):
            cfg = DefaultConfig('file.yml')

        self.assertEqual(cfg.get({}, 'source', 'foo', 'field'), 'value')
        self.assertEqual(cfg.get({}, 'source', 'foo', 'other'), None)
        self.assertEqual(cfg.get({}, 'source', 'foo', 'other', 'default'),
                         'default')

        self.assertEqual(cfg.get({}, 'source', 'bar', 'field'), None)
        self.assertEqual(cfg.get({}, 'source', 'bar', 'field', 'default'),
                         'default')

        self.assertEqual(cfg.get({}, 'usage', 'foo', 'field'), None)
        self.assertEqual(cfg.get({}, 'usage', 'foo', 'field', 'default'),
                         'default')

    def test_list_field(self):
        data = 'source:\n  foo:\n    field: [1, 2]'
        with mock.patch('builtins.open', mock_open(data)):
            cfg = DefaultConfig('file.yml')

        self.assertEqual(cfg.get({}, 'source', 'foo', 'field'), [1, 2])
        self.assertEqual(cfg.get({}, 'source', 'foo', 'other'), None)
        self.assertEqual(cfg.get({}, 'source', 'foo', 'other', []), [])
        self.assertEqual(cfg.get({}, 'source', 'bar', 'field'), None)
        self.assertEqual(cfg.get({}, 'source', 'bar', 'field', []), [])

    def test_dict_field(self):
        data = 'source:\n  foo:\n    field: {goat: 1, panda: 2}'
        with mock.patch('builtins.open', mock_open(data)):
            cfg = DefaultConfig('file.yml')

        self.assertEqual(cfg.get({}, 'source', 'foo', 'field'),
                         {'goat': 1, 'panda': 2})
        self.assertEqual(cfg.get({}, 'source', 'foo', 'other'), None)
        self.assertEqual(cfg.get({}, 'source', 'foo', 'other', {}), {})
        self.assertEqual(cfg.get({}, 'source', 'bar', 'field'), None)
        self.assertEqual(cfg.get({}, 'source', 'bar', 'field', {}), {})

    def test_expr_field(self):
        data = 'source:\n  foo:\n    field: $variable'
        with mock.patch('builtins.open', mock_open(data)):
            cfg = DefaultConfig('file.yml')

        symbols = {'variable': 'goat'}
        self.assertEqual(cfg.get(symbols, 'source', 'foo', 'field'), 'goat')
        self.assertEqual(cfg.get(symbols, 'source', 'bar', 'field'), None)

        symbols = {'variable': 'panda'}
        self.assertEqual(cfg.get(symbols, 'source', 'foo', 'field'), 'panda')
        self.assertEqual(cfg.get(symbols, 'source', 'bar', 'field'), None)

    def test_conditional(self):
        data = 'source:\n  foo:\n    - if: true\n      field: goat'
        with mock.patch('builtins.open', mock_open(data)):
            cfg = DefaultConfig('file.yml')

        self.assertEqual(cfg.get({}, 'source', 'foo', 'field'), 'goat')
        self.assertEqual(cfg.get({}, 'source', 'bar', 'field'), None)

        data = 'source:\n  foo:\n    - if: false\n      field: goat'
        with mock.patch('builtins.open', mock_open(data)):
            cfg = DefaultConfig('file.yml')

        self.assertEqual(cfg.get({}, 'source', 'foo', 'field'), None)
        self.assertEqual(cfg.get({}, 'source', 'bar', 'field'), None)

    def test_conditional_expr(self):
        data = ('source:\n  foo:\n    - if: variable == true\n' +
                '      field: goat\n    - field: panda')
        with mock.patch('builtins.open', mock_open(data)):
            cfg = DefaultConfig('file.yml')

        symbols = {'variable': True}
        self.assertEqual(cfg.get(symbols, 'source', 'foo', 'field'), 'goat')
        self.assertEqual(cfg.get(symbols, 'source', 'bar', 'field'), None)

        symbols = {'variable': False}
        self.assertEqual(cfg.get(symbols, 'source', 'foo', 'field'), 'panda')
        self.assertEqual(cfg.get(symbols, 'source', 'bar', 'field'), None)

    def test_invalid_conditional(self):
        data = ('source:\n  foo:\n    - field: goat\n    - field: panda')
        with mock.patch('builtins.open', mock_open(data)), \
             self.assertRaises(YamlParseError):
            DefaultConfig('file.yml')

    def test_invalid_genus(self):
        data = ('goofy:\n  foo:\n    field: value')
        with mock.patch('builtins.open', mock_open(data)), \
             self.assertRaises(YamlParseError):
            DefaultConfig('file.yml')

        data = ('source:\n  foo:\n    field: value')
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
