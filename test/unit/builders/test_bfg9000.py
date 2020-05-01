import os
from unittest import mock, TestCase

from . import BuilderTest
from .. import mock_open_log

from mopack.builders import Builder, BuilderOptions
from mopack.builders.bfg9000 import Bfg9000Builder
from mopack.usage.pkg_config import PkgConfigUsage
from mopack.types import Unset


class TestBfg9000Builder(BuilderTest):
    builder_type = Bfg9000Builder
    pkgdir = '/path/to/builddir/mopack'

    def pkgconfdir(self, name, pkgconfig='pkgconfig'):
        return os.path.join(self.pkgdir, 'build', name, pkgconfig)

    def check_build(self, builder, deploy_paths={}, extra_args=[],
                    usage=None):
        if usage is None:
            usage = {'type': 'pkg-config', 'path': self.pkgconfdir('foo')}

        srcdir = '/path/to/src'
        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('subprocess.check_call') as mcall:  # noqa
            self.assertEqual(builder.build(self.pkgdir, srcdir, deploy_paths),
                             usage)
            mopen.assert_called_with(os.path.join(self.pkgdir, 'foo.log'), 'w')
            mcall.assert_any_call(
                ['9k', os.path.join(self.pkgdir, 'build', 'foo')] + extra_args,
                stdout=mopen(), stderr=mopen()
            )
            mcall.assert_called_with(['ninja'], stdout=mopen(), stderr=mopen())

    def test_basic(self):
        builder = self.make_builder('foo')
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, [])
        self.assertEqual(builder.usage, PkgConfigUsage())

        self.check_build(builder)

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('subprocess.check_call') as mcall:  # noqa
            builder.deploy(self.pkgdir)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'foo-deploy.log'
            ), 'w')
            mcall.assert_called_with(['ninja', 'install'], stdout=mopen(),
                                     stderr=mopen())

    def test_extra_args(self):
        builder = self.make_builder('foo', extra_args='--extra args')
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, ['--extra', 'args'])
        self.assertEqual(builder.usage, PkgConfigUsage())

        self.check_build(builder, extra_args=['--extra', 'args'])

    def test_usage_str(self):
        builder = self.make_builder('foo', usage='pkg-config')
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, [])
        self.assertEqual(builder.usage, PkgConfigUsage())

        self.check_build(builder)

    def test_usage_full(self):
        usage = {'type': 'pkg-config', 'path': 'pkgconf'}
        builder = self.make_builder('foo', usage=usage)
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, [])
        self.assertEqual(builder.usage, PkgConfigUsage(path='pkgconf'))

        self.check_build(builder, usage={
            'type': 'pkg-config', 'path': self.pkgconfdir('foo', 'pkgconf')
        })

    def test_toolchain(self):
        builder = self.make_builder('foo', global_options={
            'toolchain': 'toolchain.bfg'
        })
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, [])
        self.assertEqual(builder.usage, PkgConfigUsage())

        self.check_build(builder, extra_args=['--toolchain', 'toolchain.bfg'])

    def test_deploy_paths(self):
        deploy_paths = {'prefix': '/usr/local', 'goofy': '/foo/bar'}
        builder = self.make_builder('foo')
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, [])
        self.assertEqual(builder.usage, PkgConfigUsage())

        self.check_build(builder, deploy_paths, extra_args=[
            '--prefix', '/usr/local'
        ])

    def test_clean(self):
        builder = self.make_builder('foo')
        srcdir = os.path.join(self.pkgdir, 'build', 'foo')

        with mock.patch('shutil.rmtree') as mrmtree:
            builder.clean(self.pkgdir)
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

    def test_rehydrate(self):
        usage = {'type': 'pkg-config', 'path': 'pkgconf'}
        builder = Bfg9000Builder('foo', extra_args='--extra args', usage=usage)
        data = builder.dehydrate()
        self.assertEqual(builder, Builder.rehydrate(data))


class TestBfg9000Options(TestCase):
    def test_default(self):
        opts = Bfg9000Builder.Options()
        self.assertIs(opts.toolchain, Unset)

    def test_toolchain(self):
        opts = Bfg9000Builder.Options()
        opts(toolchain='toolchain.bfg')
        self.assertEqual(opts.toolchain, 'toolchain.bfg')
        opts(toolchain='bad.bfg')
        self.assertEqual(opts.toolchain, 'toolchain.bfg')

        opts = Bfg9000Builder.Options()
        opts(toolchain=None)
        self.assertEqual(opts.toolchain, None)

        opts = Bfg9000Builder.Options()
        opts(toolchain='toolchain.bfg', child_config=True)
        self.assertIs(opts.toolchain, Unset)

    def test_rehydrate(self):
        opts_toolchain = Bfg9000Builder.Options()
        opts_toolchain(toolchain='toolchain.bfg')
        data = opts_toolchain.dehydrate()
        self.assertEqual(opts_toolchain, BuilderOptions.rehydrate(data))

        opts_none = Bfg9000Builder.Options()
        opts_none(toolchain=None)
        data = opts_none.dehydrate()
        self.assertEqual(opts_none, BuilderOptions.rehydrate(data))

        opts_default = Bfg9000Builder.Options()
        data = opts_default.dehydrate()
        rehydrated = BuilderOptions.rehydrate(data)
        self.assertEqual(opts_default, rehydrated)
        self.assertEqual(opts_none, rehydrated)
