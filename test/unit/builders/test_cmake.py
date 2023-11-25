import os
import subprocess
from unittest import mock

from . import BuilderTest, MockPackage, OptionsTest, through_json
from .. import mock_open_log

from mopack.builders import Builder, BuilderOptions
from mopack.builders.cmake import CMakeBuilder
from mopack.options import ExprSymbols
from mopack.origins.sdist import DirectoryPackage
from mopack.shell import ShellArguments
from mopack.types import Unset


class TestCMakeBuilder(BuilderTest):
    builder_type = CMakeBuilder
    symbols = ExprSymbols(variable='foo')

    def check_build(self, pkg, extra_args=[]):
        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.cmake.pushd'), \
             mock.patch('subprocess.run') as mcall:
            pkg.builder.build(self.metadata, pkg)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', pkg.name + '.log'
            ), 'a')
            mcall.assert_any_call(
                ['cmake', self.srcdir, '-G', 'Ninja'] + extra_args,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, check=True, env={}
            )
            mcall.assert_called_with(
                ['ninja'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, check=True, env={}
            )

    def test_basic(self):
        pkg = self.make_package_and_builder('foo')
        self.assertEqual(pkg.builder.name, 'foo')
        self.assertEqual(pkg.builder.extra_args, ShellArguments())
        self.check_build(pkg)

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.cmake.pushd'), \
             mock.patch('subprocess.run') as mcall:
            pkg.builder.deploy(self.metadata, pkg)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'deploy', 'foo.log'
            ), 'a')
            mcall.assert_called_with(
                ['ninja', 'install'],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, check=True, env={}
            )

    def test_extra_args(self):
        pkg = self.make_package_and_builder('foo', extra_args='--extra args')
        self.assertEqual(pkg.builder.name, 'foo')
        self.assertEqual(pkg.builder.extra_args,
                         ShellArguments(['--extra', 'args']))
        self.check_build(pkg, extra_args=['--extra', 'args'])

    def test_toolchain(self):
        pkg = self.make_package_and_builder('foo', this_options={
            'toolchain': 'toolchain.cmake',
        })
        self.assertEqual(pkg.builder.name, 'foo')
        self.assertEqual(pkg.builder.extra_args, ShellArguments())
        self.check_build(pkg, extra_args=[
            '-DCMAKE_TOOLCHAIN_FILE=' +
            os.path.join(self.config_dir, 'toolchain.cmake')
        ])

    def test_deploy_dirs(self):
        deploy_dirs = {'prefix': '/usr/local', 'goofy': '/foo/bar'}
        pkg = self.make_package_and_builder('foo', deploy_dirs=deploy_dirs)
        self.assertEqual(pkg.builder.name, 'foo')
        self.assertEqual(pkg.builder.extra_args, ShellArguments())
        self.check_build(pkg, extra_args=[
            '-DCMAKE_INSTALL_PREFIX:PATH=' + os.path.abspath('/usr/local')
        ])

    def test_clean(self):
        pkg = self.make_package_and_builder('foo')
        builddir = os.path.join(self.pkgdir, 'build', 'foo')

        with mock.patch('shutil.rmtree') as mrmtree:
            pkg.builder.clean(self.metadata, pkg)
            mrmtree.assert_called_once_with(builddir, ignore_errors=True)

    def test_linkage(self):
        opts = self.make_options()
        pkg = DirectoryPackage('foo', path=self.srcdir, build='cmake',
                               linkage='pkg_config', _options=opts,
                               config_file=self.config_file)
        pkg.get_linkage(self.metadata, None)

    def test_rehydrate(self):
        opts = self.make_options()
        builder = CMakeBuilder(
            MockPackage('foo', _options=opts), extra_args='--extra args',
            _symbols=self.symbols
        )
        data = through_json(builder.dehydrate())
        self.assertEqual(builder, Builder.rehydrate(data, name='foo',
                                                    _options=opts))

    def test_upgrade_from_v1(self):
        opts = self.make_options()
        data = {'type': 'cmake', '_version': 1, 'name': 'bar',
                'extra_args': []}
        with mock.patch.object(CMakeBuilder, 'upgrade',
                               side_effect=CMakeBuilder.upgrade) as m:
            builder = Builder.rehydrate(data, name='foo', _options=opts)
            self.assertIsInstance(builder, CMakeBuilder)
            m.assert_called_once()


class TestCMakeOptions(OptionsTest):
    symbols = ExprSymbols(variable='foo')

    def test_default(self):
        opts = CMakeBuilder.Options()
        self.assertIs(opts.toolchain, Unset)

    def test_toolchain(self):
        opts = CMakeBuilder.Options()
        opts(toolchain='toolchain.cmake', config_file=self.config_file,
             _symbols=self.symbols)
        self.assertEqual(opts.toolchain,
                         os.path.join(self.config_dir, 'toolchain.cmake'))
        opts(toolchain='bad.cmake', config_file=self.config_file,
             _symbols=self.symbols)
        self.assertEqual(opts.toolchain,
                         os.path.join(self.config_dir, 'toolchain.cmake'))

        opts = CMakeBuilder.Options()
        opts(toolchain='$variable/toolchain.cmake',
             config_file=self.config_file,
             _symbols=self.symbols)
        self.assertEqual(opts.toolchain, os.path.join(
            self.config_dir, 'foo', 'toolchain.cmake'
        ))

        opts = CMakeBuilder.Options()
        opts(toolchain=None, config_file=self.config_file,
             _symbols=self.symbols)
        self.assertEqual(opts.toolchain, None)

        opts = CMakeBuilder.Options()
        opts(toolchain='toolchain.cmake', config_file=self.config_file,
             _child_config=True, _symbols=self.symbols)
        self.assertIs(opts.toolchain, Unset)

    def test_rehydrate(self):
        opts_toolchain = CMakeBuilder.Options()
        opts_toolchain(toolchain='toolchain.cmake',
                       config_file=self.config_file,
                       _symbols=self.symbols)
        data = through_json(opts_toolchain.dehydrate())
        self.assertEqual(opts_toolchain, BuilderOptions.rehydrate(data))

        opts_none = CMakeBuilder.Options()
        opts_none(toolchain=None, config_file=self.config_file,
                  _symbols=self.symbols)
        data = through_json(opts_none.dehydrate())
        self.assertEqual(opts_none, BuilderOptions.rehydrate(data))

        opts_default = CMakeBuilder.Options()
        data = through_json(opts_default.dehydrate())
        rehydrated = BuilderOptions.rehydrate(data)
        self.assertEqual(opts_default, rehydrated)
        self.assertEqual(opts_none, rehydrated)

    def test_upgrade(self):
        data = {'type': 'cmake', '_version': 0, 'toolchain': None}
        o = CMakeBuilder.Options
        with mock.patch.object(o, 'upgrade', side_effect=o.upgrade) as m:
            pkg = BuilderOptions.rehydrate(data)
            self.assertIsInstance(pkg, o)
            m.assert_called_once()
