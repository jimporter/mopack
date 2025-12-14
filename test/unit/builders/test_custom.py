import os
from unittest import mock

from . import BuilderTest, MockPackage, through_json
from .. import mock_open_log, rehydrate_kwargs

from mopack.builders import Builder
from mopack.builders.custom import CustomBuilder
from mopack.origins.sdist import DirectoryPackage
from mopack.path import Path
from mopack.placeholder import placeholder as ph
from mopack.shell import ShellArguments


class TestCustomBuilder(BuilderTest):
    builder_type = CustomBuilder

    def check_build(self, pkg, build_commands=None, env={}):
        if build_commands is None:
            builddir = os.path.join(self.pkgdir, 'build', pkg.name)
            build_commands = [i.args({
                'srcdir': self.srcdir, 'builddir': builddir
            }) for i in pkg.builder.build_commands]

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.custom.pushd'), \
             mock.patch('mopack.log.LogFile.check_call') as mcall:
            pkg.builder.build(self.metadata, pkg)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', pkg.name + '.log'
            ), 'a')
            mcall.assert_has_calls([mock.call(i, env=env)
                                    for i in build_commands])

    def test_basic(self):
        pkg = self.make_package_and_builder('foo', build_commands=[
            'configure', 'make',
        ], outdir='build')
        self.assertEqual(pkg.builder.name, 'foo')
        self.assertEqual(pkg.builder.env, {})
        self.assertEqual(pkg.builder.build_commands, [
            ShellArguments(['configure']),
            ShellArguments(['make']),
        ])
        self.assertEqual(pkg.builder.deploy_commands, [])
        self.check_build(pkg)

    def test_env(self):
        pkg = self.make_package_and_builder(
            'foo', env={'VAR': 'value'}, build_commands=['configure', 'make'],
            outdir='build', pkg_args={'env': {'PKG': 'package'}},
            common_options={'env': {'GLOBAL': 'global'}}
        )
        self.assertEqual(pkg.builder.name, 'foo')
        self.assertEqual(pkg.builder.env, {'VAR': 'value'})
        self.assertEqual(pkg.builder.build_commands, [
            ShellArguments(['configure']),
            ShellArguments(['make']),
        ])
        self.assertEqual(pkg.builder.deploy_commands, [])
        self.check_build(pkg, env={
            'GLOBAL': 'global', 'PKG': 'package', 'VAR': 'value'
        })

    def test_build_list(self):
        pkg = self.make_package_and_builder('foo', build_commands=[
            ['configure', '--foo'], ['make', '-j2']
        ], outdir='build')
        self.assertEqual(pkg.builder.name, 'foo')
        self.assertEqual(pkg.builder.env, {})
        self.assertEqual(pkg.builder.build_commands, [
            ShellArguments(['configure', '--foo']),
            ShellArguments(['make', '-j2']),
        ])
        self.assertEqual(pkg.builder.deploy_commands, [])
        self.check_build(pkg)

    def test_path_objects(self):
        pkg = self.make_package_and_builder('foo', build_commands=[
            'configure $srcdir/build',
            ['make', '-C', '$builddir'],
        ], outdir='build')
        self.assertEqual(pkg.builder.name, 'foo')
        self.assertEqual(pkg.builder.env, {})
        self.assertEqual(pkg.builder.build_commands, [
            ShellArguments(['configure', ph(Path('', 'srcdir')) + '/build']),
            ShellArguments(['make', '-C', ph(Path('', 'builddir'))]),
        ])
        self.assertEqual(pkg.builder.deploy_commands, [])
        self.check_build(pkg, build_commands=[
            ['configure', self.srcdir + '/build'],
            ['make', '-C', os.path.join(self.pkgdir, 'build', 'foo')],
        ])

    def test_deploy(self):
        pkg = self.make_package_and_builder(
            'foo', build_commands=['make'], deploy_commands=['make install'],
            outdir='build'
        )
        self.assertEqual(pkg.builder.name, 'foo')
        self.assertEqual(pkg.builder.env, {})
        self.assertEqual(pkg.builder.build_commands, [
            ShellArguments(['make']),
        ])
        self.assertEqual(pkg.builder.deploy_commands, [
            ShellArguments(['make', 'install']),
        ])
        self.check_build(pkg)

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.custom.pushd'), \
             mock.patch('mopack.log.LogFile.check_call') as mcall:
            pkg.builder.deploy(self.metadata, pkg)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'deploy', 'foo.log'
            ), 'a')
            mcall.assert_called_with(['make', 'install'], env={})

    def test_cd(self):
        pkg = self.make_package_and_builder('foo', build_commands=[
            'configure $srcdir/build',
            'cd $builddir',
            'make',
        ], outdir='build')
        self.assertEqual(pkg.builder.name, 'foo')
        self.assertEqual(pkg.builder.build_commands, [
            ShellArguments(['configure', ph(Path('', 'srcdir')) + '/build']),
            ShellArguments(['cd', ph(Path('', 'builddir'))]),
            ShellArguments(['make']),
        ])

        with mock.patch('os.chdir') as mcd:
            builddir = os.path.join(self.pkgdir, 'build', 'foo')
            self.check_build(pkg, build_commands=[
                ['configure', self.srcdir + '/build'],
                ['make'],
            ])
            mcd.assert_called_once_with(builddir)

    def test_cd_invalid(self):
        pkg = self.make_package_and_builder('foo', build_commands=[
            'cd foo bar',
        ], outdir='build')

        with mock_open_log(), \
             mock.patch('mopack.builders.custom.pushd'), \
             self.assertRaises(RuntimeError):
            pkg.builder.build(self.metadata, pkg)

    def test_clean(self):
        pkg = self.make_package_and_builder('foo', build_commands=['make'],
                                            outdir='build')
        builddir = os.path.join(self.pkgdir, 'build', 'foo')

        with mock.patch('shutil.rmtree') as mrmtree:
            pkg.builder.clean(self.metadata, pkg)
            mrmtree.assert_called_once_with(builddir, ignore_errors=True)

    def test_linkage(self):
        opts = self.make_options()
        pkg = DirectoryPackage('foo', path=self.srcdir, build={
            'type': 'custom', 'build_commands': ['make'], 'outdir': 'build',
        }, linkage='pkg_config', _options=opts, config_file=self.config_file)
        self.package_fetch(pkg)
        pkg.get_linkage(self.metadata, None)

    def test_rehydrate(self):
        opts = self.make_options()
        builder = CustomBuilder(MockPackage('foo', _options=opts),
                                build_commands=['make'], outdir='build',
                                _symbols=self.symbols)
        data = through_json(builder.dehydrate())
        self.assertEqual(builder, Builder.rehydrate(
            data, name='foo', _options=opts, _symbols=opts.expr_symbols,
            **rehydrate_kwargs
        ))

    def test_upgrade_from_v1(self):
        opts = self.make_options()
        data = {'type': 'custom', '_version': 1, 'name': 'bar',
                'build_commands': [], 'deploy_commands': None}
        with mock.patch.object(CustomBuilder, 'upgrade',
                               side_effect=CustomBuilder.upgrade) as m:
            builder = Builder.rehydrate(
                data, name='foo', _options=opts, _symbols=opts.expr_symbols,
                **rehydrate_kwargs
            )
            self.assertIsInstance(builder, CustomBuilder)
            m.assert_called_once()
