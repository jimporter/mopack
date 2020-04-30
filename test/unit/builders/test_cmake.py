import os
from unittest import mock, TestCase

from . import BuilderTest
from .. import mock_open_log

from mopack.builders import Builder, BuilderOptions
from mopack.builders.cmake import CMakeBuilder
from mopack.usage.pkg_config import PkgConfigUsage
from mopack.types import Unset


class TestCMakeBuilder(BuilderTest):
    builder_type = CMakeBuilder
    pkgdir = '/path/to/builddir/mopack'

    def pkgconfdir(self, name, pkgconfig='pkgconfig'):
        return os.path.join(self.pkgdir, 'build', name, pkgconfig)

    def check_build(self, builder, deploy_paths={}, extra_args=[],
                    usage=None):
        if usage is None:
            usage = {'type': 'pkg-config', 'path': self.pkgconfdir('foo')}

        srcdir = '/path/to/src'
        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.cmake.pushd'), \
             mock.patch('subprocess.check_call') as mcall:  # noqa
            self.assertEqual(builder.build(self.pkgdir, srcdir, deploy_paths),
                             usage)
            mopen.assert_called_with(os.path.join(self.pkgdir, 'foo.log'), 'w')
            mcall.assert_any_call(['cmake', srcdir] + extra_args,
                                  stdout=mopen(), stderr=mopen())
            mcall.assert_called_with(['make'], stdout=mopen(), stderr=mopen())

    def test_basic(self):
        builder = self.make_builder('foo', usage='pkg-config')
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, [])
        self.assertEqual(builder.usage, PkgConfigUsage())

        self.check_build(builder)

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.cmake.pushd'), \
             mock.patch('subprocess.check_call') as mcall:  # noqa
            builder.deploy(self.pkgdir)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'foo-deploy.log'
            ), 'w')
            mcall.assert_called_with(['make', 'install'], stdout=mopen(),
                                     stderr=mopen())

    def test_extra_args(self):
        builder = self.make_builder('foo', extra_args='--extra args',
                                    usage='pkg-config')
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, ['--extra', 'args'])
        self.assertEqual(builder.usage, PkgConfigUsage())

        self.check_build(builder, extra_args=['--extra', 'args'])

    def test_usage_full(self):
        usage = {'type': 'pkg-config', 'path': 'pkgconf'}
        builder = self.make_builder('foo', usage=usage)
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, [])
        self.assertEqual(builder.usage, PkgConfigUsage(path='pkgconf'))

        self.check_build(builder, usage={
            'type': 'pkg-config', 'path': self.pkgconfdir('foo', 'pkgconf')
        })

    def test_deploy_paths(self):
        deploy_paths = {'prefix': '/usr/local', 'goofy': '/foo/bar'}
        builder = self.make_builder('foo', usage='pkg-config')
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, [])
        self.assertEqual(builder.usage, PkgConfigUsage())

        self.check_build(builder, deploy_paths, extra_args=[
            '-DCMAKE_INSTALL_PREFIX:PATH=/usr/local'
        ])

    def test_clean(self):
        builder = self.make_builder('foo', usage='pkg-config')
        srcdir = os.path.join(self.pkgdir, 'build', 'foo')

        with mock.patch('shutil.rmtree') as mrmtree:
            builder.clean(self.pkgdir)
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

    def test_rehydrate(self):
        usage = {'type': 'pkg-config', 'path': 'pkgconf'}
        builder = CMakeBuilder('foo', extra_args='--extra args', usage=usage)
        data = builder.dehydrate()
        self.assertEqual(builder, Builder.rehydrate(data))
