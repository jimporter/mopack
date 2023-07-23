import os
import subprocess
from unittest import mock

from . import BuilderTest, MockPackage, through_json
from .. import mock_open_log

from mopack.builders import Builder
from mopack.builders.custom import CustomBuilder
from mopack.path import Path
from mopack.shell import ShellArguments
from mopack.origins.sdist import DirectoryPackage


class TestCustomBuilder(BuilderTest):
    builder_type = CustomBuilder

    def check_build(self, builder, build_commands=None, *, pkg=None):
        if pkg is None:
            pkg = MockPackage(srcdir=self.srcdir, _options=self.make_options())
        if build_commands is None:
            builddir = os.path.join(self.pkgdir, 'build', builder.name)
            build_commands = [i.fill(srcdir=self.srcdir, builddir=builddir)
                              for i in builder.build_commands]

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.custom.pushd'), \
             mock.patch('subprocess.run') as mcall:
            builder.build(self.metadata, pkg)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'foo.log'
            ), 'a')
            for line in build_commands:
                mcall.assert_any_call(
                    line, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    universal_newlines=True, check=True, env={}
                )

    def test_basic(self):
        builder = self.make_builder('foo', build_commands=[
            'configure', 'make',
        ])
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.build_commands, [
            ShellArguments(['configure']),
            ShellArguments(['make']),
        ])
        self.assertEqual(builder.deploy_commands, [])
        self.check_build(builder)

    def test_build_list(self):
        builder = self.make_builder('foo', build_commands=[
            ['configure', '--foo'], ['make', '-j2']
        ])
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.build_commands, [
            ShellArguments(['configure', '--foo']),
            ShellArguments(['make', '-j2']),
        ])
        self.assertEqual(builder.deploy_commands, [])
        self.check_build(builder)

    def test_path_objects(self):
        builder = self.make_builder('foo', build_commands=[
            'configure $srcdir/build',
            ['make', '-C', '$builddir'],
        ])
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.build_commands, [
            ShellArguments(['configure', (Path('', 'srcdir'), '/build')]),
            ShellArguments(['make', '-C', Path('', 'builddir')]),
        ])
        self.assertEqual(builder.deploy_commands, [])
        self.check_build(builder, build_commands=[
            ['configure', self.srcdir + '/build'],
            ['make', '-C', os.path.join(self.pkgdir, 'build', 'foo')],
        ])

    def test_deploy(self):
        pkg = MockPackage(srcdir=self.srcdir, _options=self.make_options())
        builder = self.make_builder(pkg, build_commands=['make'],
                                    deploy_commands=['make install'])
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.build_commands, [
            ShellArguments(['make']),
        ])
        self.assertEqual(builder.deploy_commands, [
            ShellArguments(['make', 'install']),
        ])
        self.check_build(builder)

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.custom.pushd'), \
             mock.patch('subprocess.run') as mcall:
            builder.deploy(self.metadata, pkg)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'deploy', 'foo.log'
            ), 'a')
            mcall.assert_called_with(
                ['make', 'install'], stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, universal_newlines=True,
                check=True, env={}
            )

    def test_cd(self):
        builder = self.make_builder('foo', build_commands=[
            'configure $srcdir/build',
            'cd $builddir',
            'make',
        ])
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.build_commands, [
            ShellArguments(['configure', (Path('', 'srcdir'), '/build')]),
            ShellArguments(['cd', Path('', 'builddir')]),
            ShellArguments(['make']),
        ])

        with mock.patch('os.chdir') as mcd:
            builddir = os.path.join(self.pkgdir, 'build', 'foo')
            self.check_build(builder, build_commands=[
                ['configure', self.srcdir + '/build'],
                ['make'],
            ])
            mcd.assert_called_once_with(builddir)

    def test_cd_invalid(self):
        pkg = MockPackage(srcdir=self.srcdir, _options=self.make_options())
        builder = self.make_builder(pkg, build_commands=['cd foo bar'])

        with mock_open_log(), \
             mock.patch('mopack.builders.custom.pushd'), \
             self.assertRaises(RuntimeError):
            builder.build(self.metadata, pkg)

    def test_clean(self):
        pkg = MockPackage(srcdir=self.srcdir, _options=self.make_options())
        builder = self.make_builder(pkg, build_commands=['make'])
        builddir = os.path.join(self.pkgdir, 'build', 'foo')

        with mock.patch('shutil.rmtree') as mrmtree:
            builder.clean(self.metadata, pkg)
            mrmtree.assert_called_once_with(builddir, ignore_errors=True)

    def test_linkage(self):
        opts = self.make_options()
        pkg = DirectoryPackage('foo', path=self.srcdir, build={
            'type': 'custom', 'build_commands': ['make'],
        }, linkage='pkg_config', _options=opts, config_file=self.config_file)
        pkg.get_linkage(self.metadata, None)

    def test_rehydrate(self):
        opts = self.make_options()
        builder = CustomBuilder(MockPackage('foo', _options=opts),
                                build_commands=['make'])
        data = through_json(builder.dehydrate())
        self.assertEqual(builder, Builder.rehydrate(data, _options=opts))

    def test_upgrade(self):
        opts = self.make_options()
        data = {'type': 'custom', '_version': 0, 'name': 'foo',
                'build_commands': [], 'deploy_commands': None}
        with mock.patch.object(CustomBuilder, 'upgrade',
                               side_effect=CustomBuilder.upgrade) as m:
            pkg = Builder.rehydrate(data, _options=opts)
            self.assertIsInstance(pkg, CustomBuilder)
            m.assert_called_once()
