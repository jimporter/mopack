import os
import subprocess
from unittest import mock

from . import BuilderTest, MockPackage, OptionsTest, through_json
from .. import mock_open_log

from mopack.builders import Builder, BuilderOptions
from mopack.builders.bfg9000 import Bfg9000Builder
from mopack.shell import ShellArguments
from mopack.sources.sdist import DirectoryPackage
from mopack.types import Unset


class TestBfg9000Builder(BuilderTest):
    builder_type = Bfg9000Builder

    def check_build(self, builder, extra_args=[], *, pkg=None):
        if pkg is None:
            pkg = MockPackage(srcdir=self.srcdir, _options=self.make_options())
        builddir = os.path.join(self.pkgdir, 'build', 'foo')
        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('subprocess.run') as mcall:
            builder.build(pkg, self.pkgdir)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'foo.log'
            ), 'a')
            mcall.assert_any_call(
                ['bfg9000', 'configure', builddir] + extra_args,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, check=True
            )
            mcall.assert_called_with(
                ['ninja'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, check=True
            )

    def test_basic(self):
        pkg = MockPackage(srcdir=self.srcdir, _options=self.make_options())
        builder = self.make_builder(pkg)
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, ShellArguments())
        self.check_build(builder)

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('subprocess.run') as mcall:
            builder.deploy(pkg, self.pkgdir)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'deploy', 'foo.log'
            ), 'a')
            mcall.assert_called_with(
                ['ninja', 'install'], stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, universal_newlines=True,
                check=True
            )

    def test_extra_args(self):
        builder = self.make_builder('foo', extra_args='--extra args')
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args,
                         ShellArguments(['--extra', 'args']))
        self.check_build(builder, extra_args=['--extra', 'args'])

    def test_toolchain(self):
        builder = self.make_builder('foo', this_options={
            'toolchain': 'toolchain.bfg'
        })
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, ShellArguments())
        self.check_build(builder, extra_args=[
            '--toolchain', os.path.join(self.config_dir, 'toolchain.bfg')
        ])

    def test_deploy_paths(self):
        deploy_paths = {'prefix': '/usr/local', 'goofy': '/foo/bar'}
        builder = self.make_builder('foo', deploy_paths=deploy_paths)
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, ShellArguments())
        self.check_build(builder, extra_args=['--prefix', '/usr/local'])

    def test_clean(self):
        pkg = MockPackage(srcdir=self.srcdir, _options=self.make_options())
        builder = self.make_builder(pkg)
        builddir = os.path.join(self.pkgdir, 'build', 'foo')

        with mock.patch('shutil.rmtree') as mrmtree:
            builder.clean(pkg, self.pkgdir)
            mrmtree.assert_called_once_with(builddir, ignore_errors=True)

    def test_usage(self):
        opts = self.make_options()
        pkg = DirectoryPackage('foo', path=self.srcdir, build='bfg9000',
                               _options=opts, config_file=self.config_file)
        pkg.get_usage(None, self.pkgdir)

    def test_rehydrate(self):
        opts = self.make_options()
        builder = Bfg9000Builder(MockPackage('foo', _options=opts),
                                 extra_args='--extra args')
        data = through_json(builder.dehydrate())
        self.assertEqual(builder, Builder.rehydrate(data, _options=opts))

    def test_upgrade(self):
        opts = self.make_options()
        data = {'type': 'bfg9000', '_version': 0, 'name': 'foo',
                'extra_args': []}
        with mock.patch.object(Bfg9000Builder, 'upgrade',
                               side_effect=Bfg9000Builder.upgrade) as m:
            pkg = Builder.rehydrate(data, _options=opts)
            self.assertIsInstance(pkg, Bfg9000Builder)
            m.assert_called_once()


class TestBfg9000Options(OptionsTest):
    symbols = {'variable': 'foo'}

    def test_default(self):
        opts = Bfg9000Builder.Options()
        self.assertIs(opts.toolchain, Unset)

    def test_toolchain(self):
        opts = Bfg9000Builder.Options()
        opts(toolchain='toolchain.bfg', config_file=self.config_file,
             _symbols=self.symbols)
        self.assertEqual(opts.toolchain,
                         os.path.join(self.config_dir, 'toolchain.bfg'))
        opts(toolchain='bad.bfg', config_file=self.config_file,
             _symbols=self.symbols)
        self.assertEqual(opts.toolchain,
                         os.path.join(self.config_dir, 'toolchain.bfg'))

        opts = Bfg9000Builder.Options()
        opts(toolchain='$variable/toolchain.bfg', config_file=self.config_file,
             _symbols=self.symbols)
        self.assertEqual(opts.toolchain,
                         os.path.join(self.config_dir, 'foo', 'toolchain.bfg'))

        opts = Bfg9000Builder.Options()
        opts(toolchain=None, config_file=self.config_file,
             _symbols=self.symbols)
        self.assertEqual(opts.toolchain, None)

        opts = Bfg9000Builder.Options()
        opts(toolchain='toolchain.bfg', config_file=self.config_file,
             _child_config=True, _symbols=self.symbols)
        self.assertIs(opts.toolchain, Unset)

    def test_rehydrate(self):
        opts_toolchain = Bfg9000Builder.Options()
        opts_toolchain(toolchain='toolchain.bfg', config_file=self.config_file,
                       _symbols=self.symbols)
        data = through_json(opts_toolchain.dehydrate())
        self.assertEqual(opts_toolchain, BuilderOptions.rehydrate(data))

        opts_none = Bfg9000Builder.Options()
        opts_none(toolchain=None, config_file=self.config_file,
                  _symbols=self.symbols)
        data = through_json(opts_none.dehydrate())
        self.assertEqual(opts_none, BuilderOptions.rehydrate(data))

        opts_default = Bfg9000Builder.Options()
        data = through_json(opts_default.dehydrate())
        rehydrated = BuilderOptions.rehydrate(data)
        self.assertEqual(opts_default, rehydrated)
        self.assertEqual(opts_none, rehydrated)

    def test_upgrade(self):
        data = {'type': 'bfg9000', '_version': 0, 'toolchain': None}
        o = Bfg9000Builder.Options
        with mock.patch.object(o, 'upgrade', side_effect=o.upgrade) as m:
            pkg = BuilderOptions.rehydrate(data)
            self.assertIsInstance(pkg, o)
            m.assert_called_once()
