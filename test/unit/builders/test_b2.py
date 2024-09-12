import os
from unittest import mock

from . import BuilderTest, MockPackage, through_json
from .. import mock_open_log, rehydrate_kwargs

from mopack.builders import Builder
from mopack.builders.b2 import B2Builder
from mopack.origins.sdist import DirectoryPackage
from mopack.shell import ShellArguments


class TestB2Builder(BuilderTest):
    builder_type = B2Builder

    def check_build(self, pkg, extra_args=[], env={}):
        builddir = os.path.join(self.pkgdir, 'build', pkg.name)
        stagedir = os.path.join(builddir, 'stage')
        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.b2.pushd'), \
             mock.patch('mopack.log.LogFile.check_call') as mcall:
            pkg.builder.build(self.metadata, pkg)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', pkg.name + '.log'
            ), 'a')
            mcall.assert_called_with([
                'b2', '--build-dir=' + builddir, '--stagedir=' + stagedir
            ] + extra_args, env=env)

    def check_deploy(self, pkg, extra_args=[], env={}):
        builddir = os.path.join(self.pkgdir, 'build', pkg.name)
        stagedir = os.path.join(builddir, 'stage')
        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.b2.pushd'), \
             mock.patch('mopack.log.LogFile.check_call') as mcall:
            pkg.builder.deploy(self.metadata, pkg)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'deploy', 'foo.log'
            ), 'a')
            mcall.assert_called_with([
                'b2', 'install', '--build-dir=' + builddir,
                '--stagedir=' + stagedir
            ] + extra_args, env=env)

    def test_basic(self):
        pkg = self.make_package_and_builder('foo')
        self.assertEqual(pkg.builder.name, 'foo')
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
        self.assertEqual(pkg.builder.extra_args,
                         ShellArguments(['--extra', 'args']))
        self.check_build(pkg, extra_args=['--extra', 'args'])
        self.check_deploy(pkg, extra_args=['--extra', 'args'])

    def test_deploy_dirs(self):
        deploy_dirs = {'prefix': '/usr/local', 'goofy': '/foo/bar'}
        pkg = self.make_package_and_builder('foo', deploy_dirs=deploy_dirs)
        self.assertEqual(pkg.builder.name, 'foo')
        self.assertEqual(pkg.builder.extra_args, ShellArguments())
        self.check_build(pkg)
        self.check_deploy(pkg, extra_args=['--prefix=/usr/local'])

    def test_clean(self):
        pkg = self.make_package_and_builder('foo')
        builddir = os.path.join(self.pkgdir, 'build', pkg.name)

        with mock.patch('shutil.rmtree') as mrmtree:
            pkg.builder.clean(self.metadata, pkg)
            mrmtree.assert_called_once_with(builddir, ignore_errors=True)

    def test_linkage(self):
        opts = self.make_options()
        pkg = DirectoryPackage('foo', path=self.srcdir, build='b2',
                               linkage='pkg_config', _options=opts,
                               config_file=self.config_file)
        pkg.get_linkage(self.metadata, None)

    def test_rehydrate(self):
        opts = self.make_options()
        builder = B2Builder(
            MockPackage('foo', _options=opts), extra_args='--extra args',
            _symbols=self.symbols
        )
        data = through_json(builder.dehydrate())
        self.assertEqual(builder, Builder.rehydrate(
            data, name='foo', _options=opts, _symbols=opts.expr_symbols,
            **rehydrate_kwargs
        ))
