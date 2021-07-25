import os
import subprocess
from unittest import mock

from . import BuilderTest, MockPackage, OptionsTest, through_json
from .. import mock_open_log

from mopack.builders import Builder, BuilderOptions
from mopack.builders.cmake import CMakeBuilder
from mopack.iterutils import iterate
from mopack.shell import ShellArguments
from mopack.usage.pkg_config import PkgConfigUsage
from mopack.types import Unset


class TestCMakeBuilder(BuilderTest):
    builder_type = CMakeBuilder

    def check_build(self, builder, extra_args=[], *, submodules=None,
                    usage=None):
        if usage is None:
            pcfiles = ['foo']
            pcfiles.extend('foo_{}'.format(i) for i in iterate(submodules))
            usage = {'name': 'foo', 'type': 'pkg_config',
                     'path': self.pkgconfdir('foo'), 'pcfiles': pcfiles,
                     'extra_args': []}

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.cmake.pushd'), \
             mock.patch('subprocess.run') as mcall:  # noqa
            builder.build(self.pkgdir, self.srcdir)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'foo.log'
            ), 'a')
            mcall.assert_any_call(
                ['cmake', self.srcdir, '-G', 'Ninja'] + extra_args,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, check=True
            )
            mcall.assert_called_with(
                ['ninja'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, check=True
            )
        self.assertEqual(builder.get_usage(
            MockPackage(), submodules, self.pkgdir, self.srcdir
        ), usage)

    def test_basic(self):
        builder = self.make_builder('foo', usage='pkg_config')
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, ShellArguments())
        self.assertEqual(builder.usage, PkgConfigUsage(
            'foo', submodules=None, _options=self.make_options(),
            _path_bases=self.path_bases
        ))

        self.check_build(builder)

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.cmake.pushd'), \
             mock.patch('subprocess.run') as mcall:  # noqa
            builder.deploy(self.pkgdir, self.srcdir)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'deploy', 'foo.log'
            ), 'a')
            mcall.assert_called_with(
                ['ninja', 'install'],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, check=True
            )

    def test_extra_args(self):
        builder = self.make_builder('foo', extra_args='--extra args',
                                    usage='pkg_config')
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args,
                         ShellArguments(['--extra', 'args']))
        self.assertEqual(builder.usage, PkgConfigUsage(
            'foo', submodules=None, _options=self.make_options(),
            _path_bases=self.path_bases
        ))

        self.check_build(builder, extra_args=['--extra', 'args'])

    def test_usage_full(self):
        usage = {'type': 'pkg_config', 'path': 'pkgconf'}
        builder = self.make_builder('foo', usage=usage)
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, ShellArguments())
        self.assertEqual(builder.usage, PkgConfigUsage(
            'foo', path='pkgconf', submodules=None,
            _options=self.make_options(), _path_bases=self.path_bases
        ))

        self.check_build(builder, usage={
            'name': 'foo', 'type': 'pkg_config',
            'path': self.pkgconfdir('foo', 'pkgconf'), 'pcfiles': ['foo'],
            'extra_args': [],
        })

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        builder = self.make_builder('foo', usage='pkg_config',
                                    submodules=submodules_required)
        self.check_build(builder, submodules=['sub'], usage={
            'name': 'foo', 'type': 'pkg_config',
            'path': self.pkgconfdir('foo'), 'pcfiles': ['foo_sub'],
            'extra_args': [],
        })

        builder = self.make_builder(
            'foo', usage={'type': 'pkg_config', 'pcfile': 'bar'},
            submodules=submodules_required
        )
        self.check_build(builder, submodules=['sub'], usage={
            'name': 'foo', 'type': 'pkg_config',
            'path': self.pkgconfdir('foo'), 'pcfiles': ['bar', 'foo_sub'],
            'extra_args': [],
        })

        builder = self.make_builder('foo', usage='pkg_config',
                                    submodules=submodules_optional)
        self.check_build(builder, submodules=['sub'])

        builder = self.make_builder(
            'foo', usage={'type': 'pkg_config', 'pcfile': 'bar'},
            submodules=submodules_optional
        )
        self.check_build(builder, submodules=['sub'], usage={
            'name': 'foo', 'type': 'pkg_config',
            'path': self.pkgconfdir('foo'), 'pcfiles': ['bar', 'foo_sub'],
            'extra_args': [],
        })

    def test_toolchain(self):
        builder = self.make_builder(
            'foo', usage={'type': 'pkg_config'},
            this_options={'toolchain': 'toolchain.cmake'}
        )
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, ShellArguments())
        self.assertEqual(builder.usage, PkgConfigUsage(
            'foo', submodules=None, _options=self.make_options(),
            _path_bases=self.path_bases
        ))

        self.check_build(builder, extra_args=[
            '-DCMAKE_TOOLCHAIN_FILE=' +
            os.path.join(self.config_dir, 'toolchain.cmake')
        ])

    def test_deploy_paths(self):
        deploy_paths = {'prefix': '/usr/local', 'goofy': '/foo/bar'}
        builder = self.make_builder('foo', usage='pkg_config',
                                    deploy_paths=deploy_paths)
        self.assertEqual(builder.name, 'foo')
        self.assertEqual(builder.extra_args, ShellArguments())
        self.assertEqual(builder.usage, PkgConfigUsage(
            'foo', submodules=None, _options=self.make_options(),
            _path_bases=self.path_bases
        ))

        self.check_build(builder, extra_args=[
            '-DCMAKE_INSTALL_PREFIX:PATH=' + os.path.abspath('/usr/local')
        ])

    def test_clean(self):
        builder = self.make_builder('foo', usage='pkg_config')
        srcdir = os.path.join(self.pkgdir, 'build', 'foo')

        with mock.patch('shutil.rmtree') as mrmtree:
            builder.clean(self.pkgdir)
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

    def test_rehydrate(self):
        opts = self.make_options()
        builder = CMakeBuilder('foo', extra_args='--extra args',
                               submodules=None, _options=opts)
        builder.set_usage({'type': 'pkg_config', 'path': 'pkgconf'},
                          submodules=None)
        data = through_json(builder.dehydrate())
        self.assertEqual(builder, Builder.rehydrate(data, _options=opts))

    def test_upgrade(self):
        opts = self.make_options()
        data = {'type': 'cmake', '_version': 0, 'name': 'foo',
                'extra_args': [], 'usage': {'type': 'system', '_version': 0}}
        with mock.patch.object(CMakeBuilder, 'upgrade',
                               side_effect=CMakeBuilder.upgrade) as m:
            pkg = Builder.rehydrate(data, _options=opts)
            self.assertIsInstance(pkg, CMakeBuilder)
            m.assert_called_once()


class TestCMakeOptions(OptionsTest):
    symbols = {'variable': 'foo'}

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
