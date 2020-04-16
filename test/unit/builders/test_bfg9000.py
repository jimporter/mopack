from unittest import TestCase

from mopack.builders.bfg9000 import Bfg9000Builder


class TestBfg9000Builder(TestCase):
    def test_basic(self):
        builder = Bfg9000Builder('foo')
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, [])

    def test_extra_args(self):
        builder = Bfg9000Builder('foo', extra_args='--extra args')
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, ['--extra', 'args'])
