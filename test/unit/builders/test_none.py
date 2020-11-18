import os
from unittest import mock

from . import BuilderTest

from mopack.builders import Builder
from mopack.builders.none import NoneBuilder
from mopack.iterutils import iterate
from mopack.usage import make_usage
from mopack.usage.pkg_config import PkgConfigUsage


class TestNoneBuilder(BuilderTest):
    builder_type = NoneBuilder
    pkgdir = os.path.abspath('/path/to/builddir/mopack')

    def pkgconfdir(self, name, pkgconfig='pkgconfig'):
        return os.path.join(self.pkgdir, 'build', name, pkgconfig)

    def check_build(self, builder, deploy_paths={}, extra_args=[], *,
                    submodules=None, usage=None):
        if usage is None:
            pcfiles = ['foo']
            pcfiles.extend('foo_{}'.format(i) for i in iterate(submodules))
            usage = {'type': 'pkg-config', 'path': self.pkgconfdir('foo'),
                     'pcfiles': pcfiles, 'extra_args': []}

        srcdir = '/path/to/src'
        with mock.patch('subprocess.run') as mcall:
            builder.build(self.pkgdir, srcdir, deploy_paths)
            mcall.assert_not_called()
        self.assertEqual(builder.get_usage(self.pkgdir, submodules, srcdir),
                         usage)

    def test_basic(self):
        builder = self.make_builder('foo', usage='pkg-config')
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.usage, PkgConfigUsage('foo', submodules=None))

        self.check_build(builder)

        with mock.patch('subprocess.run') as mcall:
            builder.deploy(self.pkgdir)
            mcall.assert_not_called()

    def test_usage_full(self):
        usage = {'type': 'pkg-config', 'path': 'pkgconf'}
        builder = self.make_builder('foo', usage=usage)
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.usage, PkgConfigUsage('foo', path='pkgconf',
                                                       submodules=None))

        self.check_build(builder, usage={
            'type': 'pkg-config', 'path': self.pkgconfdir('foo', 'pkgconf'),
            'pcfiles': ['foo'], 'extra_args': [],
        })

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        builder = self.make_builder('foo', usage='pkg-config',
                                    submodules=submodules_required)
        self.check_build(builder, submodules=['sub'], usage={
            'type': 'pkg-config', 'path': self.pkgconfdir('foo'),
            'pcfiles': ['foo_sub'], 'extra_args': [],
        })

        builder = self.make_builder(
            'foo', usage={'type': 'pkg-config', 'pcfile': 'bar'},
            submodules=submodules_required
        )
        self.check_build(builder, submodules=['sub'], usage={
            'type': 'pkg-config', 'path': self.pkgconfdir('foo'),
            'pcfiles': ['bar', 'foo_sub'], 'extra_args': [],
        })

        builder = self.make_builder('foo', usage='pkg-config',
                                    submodules=submodules_optional)
        self.check_build(builder, submodules=['sub'])

        builder = self.make_builder(
            'foo', usage={'type': 'pkg-config', 'pcfile': 'bar'},
            submodules=submodules_optional
        )
        self.check_build(builder, submodules=['sub'], usage={
            'type': 'pkg-config', 'path': self.pkgconfdir('foo'),
            'pcfiles': ['bar', 'foo_sub'], 'extra_args': [],
        })

    def test_clean(self):
        builder = self.make_builder('foo', usage='pkg-config')

        with mock.patch('shutil.rmtree') as mrmtree:
            builder.clean(self.pkgdir)
            mrmtree.assert_not_called()

    def test_rehydrate(self):
        usage = make_usage('foo', {'type': 'pkg-config', 'path': 'pkgconf'},
                           submodules=None)
        builder = NoneBuilder('foo', usage=usage, submodules=None)
        data = builder.dehydrate()
        self.assertEqual(builder, Builder.rehydrate(data))
