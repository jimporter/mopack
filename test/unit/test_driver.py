import argparse
from unittest import TestCase

from mopack import driver


class TestKeyValueAction(TestCase):
    def setUp(self):
        self.action = driver.KeyValueAction(['-f', '--foo'], 'dest')

    def test_single(self):
        args = argparse.Namespace(dest=None)
        self.action(None, args, 'goat=baah')
        self.assertEqual(args, argparse.Namespace(dest={'goat': 'baah'}))

    def test_multiple(self):
        args = argparse.Namespace(dest=None)
        self.action(None, args, 'goat=baah')
        self.action(None, args, 'cow=moo')
        self.action(None, args, 'goat=baah!')
        self.assertEqual(args, argparse.Namespace(dest={
            'goat': 'baah!', 'cow': 'moo'
        }))

    def test_invalid(self):
        args = argparse.Namespace(dest=None)
        with self.assertRaises(argparse.ArgumentError):
            self.action(None, args, 'goat')


class TestConfigOptionAction(TestCase):
    def setUp(self):
        self.action = driver.ConfigOptionAction(['-f', '--foo'], 'dest')

    def test_single(self):
        args = argparse.Namespace(dest=None)
        self.action(None, args, 'goat=baah')
        self.assertEqual(args, argparse.Namespace(dest={'goat': 'baah'}))

    def test_nested(self):
        args = argparse.Namespace(dest=None)
        self.action(None, args, 'mammal:goat=baah')
        self.assertEqual(args, argparse.Namespace(dest={
            'mammal': {'goat': 'baah'}
        }))

    def test_key(self):
        action = driver.ConfigOptionAction(['-f', '--foo'], 'dest',
                                           key=['mammal'])

        args = argparse.Namespace(dest=None)
        action(None, args, 'goat=baah')
        self.assertEqual(args, argparse.Namespace(dest={
            'mammal': {'goat': 'baah'}
        }))

    def test_yaml(self):
        args = argparse.Namespace(dest=None)
        self.action(None, args, 'mammal:goat={"sound": "baah"}')
        self.assertEqual(args, argparse.Namespace(dest={
            'mammal': {'goat': {'sound': 'baah'}}
        }))

    def test_multiple(self):
        args = argparse.Namespace(dest=None)
        self.action(None, args, 'mammal:goat=- baah')
        self.action(None, args, 'mammal:cow=moo')
        self.action(None, args, 'mammal:goat=- baah!')
        self.assertEqual(args, argparse.Namespace(dest={
            'mammal': {'goat': ['baah', 'baah!'], 'cow': 'moo'}
        }))

    def test_invalid(self):
        args = argparse.Namespace(dest=None)
        with self.assertRaises(argparse.ArgumentError):
            self.action(None, args, 'goat')
        with self.assertRaises(argparse.ArgumentError):
            self.action(None, args, 'goat={')
