from unittest import TestCase

from mopack import arguments


class TestParser(TestCase):
    def test_complete(self):
        p = arguments.ArgumentParser()
        arg = p.add_argument('--arg', complete='file')
        self.assertEqual(arg.complete, 'file')

    def test_complete_group(self):
        p = arguments.ArgumentParser()
        g = p.add_argument_group()
        arg = g.add_argument('--arg', complete='file')
        self.assertEqual(arg.complete, 'file')

    def test_complete_action(self):
        class MyAction(arguments.Action):
            def __call__(self, parser, namespace, values, option_string=None):
                setattr(namespace, self.dest, values.upper())

        p = arguments.ArgumentParser()
        arg = p.add_argument('--arg', action=MyAction, complete='file')
        self.assertEqual(arg.complete, 'file')
        self.assertEqual(p.parse_args(['--arg=foo']),
                         arguments.Namespace(arg='FOO'))


class TestKeyValueAction(TestCase):
    def setUp(self):
        self.action = arguments.KeyValueAction(['-f', '--foo'], 'dest')

    def test_single(self):
        args = arguments.Namespace(dest=None)
        self.action(None, args, 'goat=baah')
        self.assertEqual(args, arguments.Namespace(dest={'goat': 'baah'}))

    def test_multiple(self):
        args = arguments.Namespace(dest=None)
        self.action(None, args, 'goat=baah')
        self.action(None, args, 'cow=moo')
        self.action(None, args, 'goat=baah!')
        self.assertEqual(args, arguments.Namespace(dest={
            'goat': 'baah!', 'cow': 'moo'
        }))

    def test_invalid(self):
        args = arguments.Namespace(dest=None)
        with self.assertRaises(arguments.ArgumentError):
            self.action(None, args, 'goat')


class TestConfigOptionAction(TestCase):
    def setUp(self):
        self.action = arguments.ConfigOptionAction(['-f', '--foo'], 'dest')

    def test_single(self):
        args = arguments.Namespace(dest=None)
        self.action(None, args, 'goat=baah')
        self.assertEqual(args, arguments.Namespace(dest={'goat': 'baah'}))

    def test_nested(self):
        args = arguments.Namespace(dest=None)
        self.action(None, args, 'mammal:goat=baah')
        self.assertEqual(args, arguments.Namespace(dest={
            'mammal': {'goat': 'baah'}
        }))

    def test_key(self):
        action = arguments.ConfigOptionAction(['-f', '--foo'], 'dest',
                                              key=['mammal'])

        args = arguments.Namespace(dest=None)
        action(None, args, 'goat=baah')
        self.assertEqual(args, arguments.Namespace(dest={
            'mammal': {'goat': 'baah'}
        }))

    def test_yaml(self):
        args = arguments.Namespace(dest=None)
        self.action(None, args, 'mammal:goat={"sound": "baah"}')
        self.assertEqual(args, arguments.Namespace(dest={
            'mammal': {'goat': {'sound': 'baah'}}
        }))

    def test_multiple(self):
        args = arguments.Namespace(dest=None)
        self.action(None, args, 'mammal:goat=- baah')
        self.action(None, args, 'mammal:cow=moo')
        self.action(None, args, 'mammal:goat=- baah!')
        self.assertEqual(args, arguments.Namespace(dest={
            'mammal': {'goat': ['baah', 'baah!'], 'cow': 'moo'}
        }))

    def test_invalid(self):
        args = arguments.Namespace(dest=None)
        with self.assertRaises(arguments.ArgumentError):
            self.action(None, args, 'goat')
        with self.assertRaises(arguments.ArgumentError):
            self.action(None, args, 'goat={')
