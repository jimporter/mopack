from unittest import TestCase

from mopack.builders import Builder
from mopack.builders.bfg9000 import Bfg9000Builder
from mopack.usage.pkgconfig import PkgConfigUsage


class TestBfg9000Builder(TestCase):
    def test_basic(self):
        builder = Bfg9000Builder('foo')
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, [])
        self.assertEqual(builder.usage, PkgConfigUsage())

    def test_extra_args(self):
        builder = Bfg9000Builder('foo', extra_args='--extra args')
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, ['--extra', 'args'])
        self.assertEqual(builder.usage, PkgConfigUsage())

    def test_usage_str(self):
        builder = Bfg9000Builder('foo', usage='pkgconfig')
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, [])
        self.assertEqual(builder.usage, PkgConfigUsage())

    def test_usage_full(self):
        usage = {'type': 'pkgconfig', 'path': 'pkgconf'}
        builder = Bfg9000Builder('foo', usage=usage)
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, [])
        self.assertEqual(builder.usage, PkgConfigUsage(path='pkgconf'))

    def test_rehydrate(self):
        usage = {'type': 'pkgconfig', 'path': 'pkgconf'}
        builder = Bfg9000Builder('foo', extra_args='--extra args', usage=usage)
        data = builder.dehydrate()
        self.assertEqual(builder, Builder.rehydrate(data))
