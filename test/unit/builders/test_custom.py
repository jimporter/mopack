import os
import subprocess
from unittest import mock

from . import BuilderTest, through_json
from .. import mock_open_log

from mopack.builders import Builder
from mopack.builders.custom import CustomBuilder
from mopack.iterutils import iterate
from mopack.path import Path
from mopack.shell import ShellArguments
from mopack.usage.pkg_config import PkgConfigUsage


class TestCustomBuilder(BuilderTest):
    builder_type = CustomBuilder
    srcdir = os.path.abspath('/path/to/src')
    pkgdir = os.path.abspath('/path/to/builddir/mopack')
    path_bases = ('srcdir', 'builddir')

    def pkgconfdir(self, name, pkgconfig='pkgconfig'):
        return os.path.join(self.pkgdir, 'build', name, pkgconfig)

    def check_build(self, builder, build_commands=None, *, submodules=None,
                    usage=None):
        if usage is None:
            pcfiles = ['foo']
            pcfiles.extend('foo_{}'.format(i) for i in iterate(submodules))
            usage = {'type': 'pkg-config', 'path': self.pkgconfdir('foo'),
                     'pcfiles': pcfiles, 'extra_args': []}
        if build_commands is None:
            builddir = os.path.join(self.pkgdir, 'build', builder.name)
            build_commands = [i.fill(srcdir=self.srcdir, builddir=builddir)
                              for i in builder.build_commands]

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.custom.pushd'), \
             mock.patch('subprocess.run') as mcall:  # noqa
            builder.build(self.pkgdir, self.srcdir)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'foo.log'
            ), 'a')
            for line in build_commands:
                mcall.assert_any_call(line, stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT,
                                      universal_newlines=True, check=True)
        self.assertEqual(builder.get_usage(
            self.pkgdir, submodules, self.srcdir
        ), usage)

    def test_basic(self):
        builder = self.make_builder('foo', build_commands=[
            'configure', 'make'
        ], usage='pkg-config')
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.build_commands, [
            ShellArguments(['configure']),
            ShellArguments(['make']),
        ])
        self.assertEqual(builder.usage, PkgConfigUsage(
            'foo', submodules=None, _options=self.make_options(),
            _path_bases=self.path_bases
        ))

        self.check_build(builder)

    def test_build_list(self):
        builder = self.make_builder('foo', build_commands=[
            ['configure', '--foo'], ['make', '-j2']
        ], usage='pkg-config')
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.build_commands, [
            ShellArguments(['configure', '--foo']),
            ShellArguments(['make', '-j2']),
        ])
        self.assertEqual(builder.usage, PkgConfigUsage(
            'foo', submodules=None, _options=self.make_options(),
            _path_bases=self.path_bases
        ))

        self.check_build(builder)

    def test_path_objects(self):
        opts = self.make_options()

        builder = self.make_builder('foo', build_commands=[
            'configure $srcdir/build',
            ['make', '-C', '$builddir'],
        ], usage='pkg-config')
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.build_commands, [
            ShellArguments(['configure', (Path('srcdir', ''), '/build')]),
            ShellArguments(['make', '-C', Path('builddir', '')]),
        ])
        self.assertEqual(builder.usage, PkgConfigUsage(
            'foo', submodules=None, _options=opts, _path_bases=self.path_bases
        ))

        self.check_build(builder, build_commands=[
            ['configure', self.srcdir + '/build'],
            ['make', '-C', os.path.join(self.pkgdir, 'build', 'foo')],
        ])

    def test_usage_full(self):
        builder = self.make_builder(
            'foo', build_commands=['make'],
            usage={'type': 'pkg-config', 'path': 'pkgconf'}
        )
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.build_commands, [
            ShellArguments(['make']),
        ])
        self.assertEqual(builder.usage, PkgConfigUsage(
            'foo', path='pkgconf', submodules=None,
            _options=self.make_options(), _path_bases=self.path_bases
        ))

        self.check_build(builder, usage={
            'type': 'pkg-config', 'path': self.pkgconfdir('foo', 'pkgconf'),
            'pcfiles': ['foo'], 'extra_args': [],
        })

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        builder = self.make_builder(
            'foo', build_commands=['make'], usage='pkg-config',
            submodules=submodules_required
        )
        self.check_build(builder, submodules=['sub'], usage={
            'type': 'pkg-config', 'path': self.pkgconfdir('foo'),
            'pcfiles': ['foo_sub'], 'extra_args': [],
        })

        builder = self.make_builder(
            'foo', build_commands=['make'],
            usage={'type': 'pkg-config', 'pcfile': 'bar'},
            submodules=submodules_required
        )
        self.check_build(builder, submodules=['sub'], usage={
            'type': 'pkg-config', 'path': self.pkgconfdir('foo'),
            'pcfiles': ['bar', 'foo_sub'], 'extra_args': [],
        })

        builder = self.make_builder(
            'foo', build_commands=['make'], usage='pkg-config',
            submodules=submodules_optional
        )
        self.check_build(builder, submodules=['sub'])

        builder = self.make_builder(
            'foo', build_commands=['make'],
            usage={'type': 'pkg-config', 'pcfile': 'bar'},
            submodules=submodules_optional
        )
        self.check_build(builder, submodules=['sub'], usage={
            'type': 'pkg-config', 'path': self.pkgconfdir('foo'),
            'pcfiles': ['bar', 'foo_sub'], 'extra_args': [],
        })

    def test_clean(self):
        builder = self.make_builder('foo', build_commands=['make'],
                                    usage='pkg-config')
        srcdir = os.path.join(self.pkgdir, 'build', 'foo')

        with mock.patch('shutil.rmtree') as mrmtree:
            builder.clean(self.pkgdir)
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

    def test_rehydrate(self):
        opts = self.make_options()
        builder = CustomBuilder('foo', build_commands=['make'],
                                submodules=None, _options=opts)
        builder.set_usage({'type': 'pkg-config', 'path': 'pkgconf'},
                          submodules=None)
        data = through_json(builder.dehydrate())
        self.assertEqual(builder, Builder.rehydrate(data, _options=opts))
