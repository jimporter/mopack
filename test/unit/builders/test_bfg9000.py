import os
from unittest import mock

from . import BuilderTest, MockPackage, OptionsTest, through_json
from .. import mock_open_log, rehydrate_kwargs

from mopack.builders import Builder, BuilderOptions
from mopack.builders.bfg9000 import Bfg9000Builder
from mopack.options import ExprSymbols
from mopack.origins.sdist import DirectoryPackage
from mopack.shell import ShellArguments
from mopack.objutils import Unset


class TestBfg9000Builder(BuilderTest):
    builder_type = Bfg9000Builder

    def check_build(self, pkg, extra_args=[], env={}):
        builddir = os.path.join(self.pkgdir, 'build', pkg.name)
        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('mopack.builders.ninja.pushd'), \
             mock.patch('mopack.log.LogFile.check_call') as mcall:
            pkg.builder.build(self.metadata, pkg)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', pkg.name + '.log'
            ), 'a')
            mcall.assert_has_calls([
                mock.call(['bfg9000', 'configure', builddir] + extra_args,
                          env=env),
                mock.call(['ninja'], env=env)
            ])

    def check_deploy(self, pkg, env={}):
        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('mopack.builders.ninja.pushd'), \
             mock.patch('mopack.log.LogFile.check_call') as mcall:
            pkg.builder.deploy(self.metadata, pkg)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'deploy', 'foo.log'
            ), 'a')
            mcall.assert_called_with(['ninja', 'install'], env=env)

    def test_basic(self):
        pkg = self.make_package_and_builder('foo')
        self.assertEqual(pkg.builder.name, 'foo')
        self.assertEqual(pkg.builder.env, {})
        self.assertEqual(pkg.builder.extra_args, ShellArguments())
        self.check_build(pkg)
        self.check_deploy(pkg)

    def test_env(self):
        pkg = self.make_package_and_builder(
            'foo', env={'VAR': 'value'}, pkg_args={'env': {'PKG': 'package'}},
            common_options={'env': {'GLOBAL': 'global'}}
        )
        self.assertEqual(pkg.builder.name, 'foo')
        self.assertEqual(pkg.builder.env, {'VAR': 'value'})
        self.assertEqual(pkg.builder.extra_args, ShellArguments())

        env = {'GLOBAL': 'global', 'PKG': 'package', 'VAR': 'value'}
        self.check_build(pkg, env=env)
        self.check_deploy(pkg, env=env)

    def test_extra_args(self):
        pkg = self.make_package_and_builder('foo', extra_args='--extra args')
        self.assertEqual(pkg.builder.name, 'foo')
        self.assertEqual(pkg.builder.env, {})
        self.assertEqual(pkg.builder.extra_args,
                         ShellArguments(['--extra', 'args']))
        self.check_build(pkg, extra_args=['--extra', 'args'])
        self.check_deploy(pkg)

    def test_toolchain(self):
        pkg = self.make_package_and_builder('foo', this_options={
            'toolchain': 'toolchain.bfg',
        })
        self.assertEqual(pkg.builder.name, 'foo')
        self.assertEqual(pkg.builder.env, {})
        self.assertEqual(pkg.builder.extra_args, ShellArguments())
        self.check_build(pkg, extra_args=[
            '--toolchain', os.path.join(self.config_dir, 'toolchain.bfg')
        ])
        self.check_deploy(pkg)

    def test_deploy_dirs(self):
        deploy_dirs = {'prefix': '/usr/local', 'goofy': '/foo/bar'}
        pkg = self.make_package_and_builder('foo', deploy_dirs=deploy_dirs)
        self.assertEqual(pkg.builder.name, 'foo')
        self.assertEqual(pkg.builder.env, {})
        self.assertEqual(pkg.builder.extra_args, ShellArguments())
        self.check_build(pkg, extra_args=['--prefix', '/usr/local'])
        self.check_deploy(pkg)

    def test_clean(self):
        pkg = self.make_package_and_builder('foo')
        builddir = os.path.join(self.pkgdir, 'build', 'foo')

        with mock.patch('shutil.rmtree') as mrmtree:
            pkg.builder.clean(self.metadata, pkg)
            mrmtree.assert_called_once_with(builddir, ignore_errors=True)

    def test_linkage(self):
        opts = self.make_options()
        pkg = DirectoryPackage('foo', path=self.srcdir, build='bfg9000',
                               _options=opts, config_file=self.config_file)
        self.package_fetch(pkg)
        pkg.get_linkage(self.metadata, None)

    def test_rehydrate(self):
        opts = self.make_options()
        builder = Bfg9000Builder(
            MockPackage('foo', _options=opts), extra_args='--extra args',
            _symbols=self.symbols
        )
        data = through_json(builder.dehydrate())
        self.assertEqual(builder, Builder.rehydrate(
            data, name='foo', _options=opts, _symbols=opts.expr_symbols,
            **rehydrate_kwargs
        ))

    def test_upgrade_from_v1(self):
        opts = self.make_options()
        data = {'type': 'bfg9000', '_version': 1, 'name': 'bar',
                'extra_args': []}
        with mock.patch.object(Bfg9000Builder, 'upgrade',
                               side_effect=Bfg9000Builder.upgrade) as m:
            builder = Builder.rehydrate(
                data, name='foo', _options=opts, _symbols=opts.expr_symbols,
                **rehydrate_kwargs
            )
            self.assertIsInstance(builder, Bfg9000Builder)
            m.assert_called_once()


class TestBfg9000Options(OptionsTest):
    symbols = ExprSymbols(variable='foo')

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
        self.assertEqual(opts_toolchain, BuilderOptions.rehydrate(
            data, **rehydrate_kwargs
        ))

        opts_none = Bfg9000Builder.Options()
        opts_none(toolchain=None, config_file=self.config_file,
                  _symbols=self.symbols)
        data = through_json(opts_none.dehydrate())
        self.assertEqual(opts_none, BuilderOptions.rehydrate(
            data, **rehydrate_kwargs
        ))

        opts_default = Bfg9000Builder.Options()
        data = through_json(opts_default.dehydrate())
        rehydrated = BuilderOptions.rehydrate(data, **rehydrate_kwargs)
        self.assertEqual(opts_default, rehydrated)
        self.assertEqual(opts_none, rehydrated)

    def test_upgrade(self):
        data = {'type': 'bfg9000', '_version': 0, 'toolchain': None}
        o = Bfg9000Builder.Options
        with mock.patch.object(o, 'upgrade', side_effect=o.upgrade) as m:
            pkg = BuilderOptions.rehydrate(data, **rehydrate_kwargs)
            self.assertIsInstance(pkg, o)
            m.assert_called_once()
