import os
import subprocess
import yaml
from io import StringIO
from unittest import mock

from . import *
from ... import assert_logging, mock_open_data
from .... import *

from mopack.builders.bfg9000 import Bfg9000Builder
from mopack.builders.none import NoneBuilder
from mopack.config import Config
from mopack.linkages.path_system import SystemLinkage
from mopack.origins import Package
from mopack.origins.apt import AptPackage
from mopack.origins.sdist import DirectoryPackage
from mopack.path import Path
from mopack.types import ConfigurationError, FieldError
from mopack.yaml_tools import SafeLineLoader, YamlParseError


def mock_isdir(p):
    return os.path.basename(p) != 'mopack.yml'


def mock_exists(p):
    return os.path.basename(p) == 'mopack.yml'


class TestDirectory(SDistTestCase):
    pkg_type = DirectoryPackage
    srcpath = os.path.join(test_data_dir, 'hello-bfg')

    def setUp(self):
        super().setUp()
        self.config = Config([])

    def test_resolve(self):
        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000')
        builder = self.make_builder(Bfg9000Builder, pkg)
        self.assertEqual(pkg.path, Path(self.srcpath))
        self.assertEqual(pkg.builders, [builder])
        self.assertEqual(pkg.needs_dependencies, True)
        self.assertEqual(pkg.should_deploy, True)

        with assert_logging([('fetch', 'foo from {}'.format(self.srcpath))]):
            pkg.fetch(self.metadata, self.config)
        self.check_resolve(pkg)

    def test_build(self):
        build = {'type': 'bfg9000', 'extra_args': '--extra'}
        pkg = self.make_package('foo', path=self.srcpath, build=build,
                                linkage='pkg_config')
        builder = self.make_builder(Bfg9000Builder, pkg, extra_args='--extra')
        self.assertEqual(pkg.path, Path(self.srcpath))
        self.assertEqual(pkg.builders, [builder])
        self.assertEqual(pkg.should_deploy, True)

        with assert_logging([('fetch', 'foo from {}'.format(self.srcpath))]):
            pkg.fetch(self.metadata, self.config)
        self.check_resolve(pkg)

    def test_build_duplicate_base(self):
        msg = "'builddir' already defined by 'bfg9000' builder"
        with self.assertRaisesRegex(TypeError, msg):
            self.make_package(
                'foo', path=self.srcpath, build=['bfg9000', 'cmake'],
                linkage='pkg_config'
            )

    def test_infer_build(self):
        mock_open = mock_open_data(
            'export:\n  build: bfg9000'
        )

        # Basic inference
        pkg = self.make_package('foo', path=self.srcpath)
        self.assertEqual(pkg.builders, None)

        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock_open):
            with assert_logging([('fetch',
                                  'foo from {}'.format(self.srcpath))]):
                config = pkg.fetch(self.metadata, self.config)
            self.assertEqual(config.export.build, 'bfg9000')
            self.assertEqual(pkg, self.make_package(
                'foo', path=self.srcpath, build='bfg9000'
            ))
        self.check_resolve(pkg)

        # Infer but override linkage
        pkg = self.make_package('foo', path=self.srcpath,
                                linkage={'type': 'system'})
        self.assertEqual(pkg.builders, None)

        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock_open):
            with assert_logging([('fetch',
                                  'foo from {}'.format(self.srcpath))]):
                config = pkg.fetch(self.metadata, self.config)
            self.assertEqual(config.export.build, 'bfg9000')
            self.assertEqual(pkg, self.make_package(
                'foo', path=self.srcpath, build='bfg9000',
                linkage={'type': 'system'}
            ))
        with mock.patch('subprocess.run', side_effect=OSError()), \
             mock.patch('os.makedirs'), \
             mock.patch('mopack.linkages.path_system.PathLinkage._filter_path',
                        lambda *args: []), \
             mock.patch('mopack.linkages.path_system.file_outdated',
                        return_value=True), \
             mock.patch('builtins.open'):
            self.check_resolve(pkg, linkage={
                'name': 'foo', 'type': 'system', 'generated': True,
                'auto_link': False, 'pcnames': ['foo'],
                'pkg_config_path': [self.pkgconfdir(None)],
            })

    def test_infer_build_override(self):
        pkg = self.make_package('foo', path=self.srcpath, build='cmake',
                                linkage='pkg_config')

        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock_open_data(
                 'export:\n  build: bfg9000'
             )):
            with assert_logging([('fetch',
                                  'foo from {}'.format(self.srcpath))]):
                config = pkg.fetch(self.metadata, self.config)
            self.assertEqual(config.export.build, 'bfg9000')
            self.assertEqual(pkg, self.make_package(
                'foo', path=self.srcpath, build='cmake', linkage='pkg_config'
            ))
        with mock.patch('mopack.builders.cmake.pushd'):
            self.check_resolve(pkg)

    def test_infer_submodules(self):
        data = 'export:\n  submodules: [french, english]\n  build: bfg9000'
        mock_open = mock_open_data(data)

        srcpath = os.path.join(test_data_dir, 'hello-multi-bfg')
        pkg = self.make_package('foo', path=srcpath)
        self.assertEqual(pkg.builders, None)

        builder = self.make_builder(Bfg9000Builder, pkg)
        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock_open):
            with assert_logging([('fetch', 'foo from {}'.format(srcpath))]):
                config = pkg.fetch(self.metadata, self.config)
            self.assertEqual(config.export.build, 'bfg9000')
            self.assertEqual(config.export.submodules,
                             ['french', 'english'])
            self.assertEqual(pkg.builders, [builder])
        self.check_resolve(pkg, submodules=['french'])

        pkg = self.make_package('foo', path=srcpath, submodules=['sub'])
        self.assertEqual(pkg.builders, None)

        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock_open):
            with assert_logging([('fetch', 'foo from {}'.format(srcpath))]):
                config = pkg.fetch(self.metadata, self.config)
            self.assertEqual(config.export.build, 'bfg9000')
            self.assertEqual(config.export.submodules,
                             ['french', 'english'])
            self.assertEqual(pkg.builders, [builder])
        self.check_resolve(pkg, submodules=['sub'])

    def test_infer_build_invalid(self):
        pkg = self.make_package('foo', path=self.srcpath)
        child = ''
        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock_open_data(child)), \
             assert_logging([('fetch', 'foo from {}'.format(self.srcpath))]), \
             self.assertRaises(ConfigurationError):
            pkg.fetch(self.metadata, self.config)

        pkg = self.make_package('foo', path=self.srcpath)
        child = 'export:\n  build: unknown'
        loc = 'line 2, column 10'
        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open',
                        lambda *args, **kwargs: StringIO(child)), \
             assert_logging([('fetch', 'foo from {}'.format(self.srcpath))]), \
             self.assertRaisesRegex(YamlParseError, loc):
            pkg.fetch(self.metadata, self.config)

        pkg = self.make_package('foo', path=self.srcpath)
        child = 'export:\n  build:\n    type: bfg9000\n    unknown: blah'
        loc = 'line 4, column 5'
        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock_open_data(child)), \
             assert_logging([('fetch', 'foo from {}'.format(self.srcpath))]), \
             self.assertRaisesRegex(YamlParseError, loc):
            pkg.fetch(self.metadata, self.config)

        pkg = self.make_package('foo', path=self.srcpath)
        child = 'export:\n  build: bfg9000\n  linkage: unknown'
        loc = 'line 3, column 10'
        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock_open_data(child)), \
             assert_logging([('fetch', 'foo from {}'.format(self.srcpath))]), \
             self.assertRaises(YamlParseError):
            pkg.fetch(self.metadata, self.config)

        pkg = self.make_package('foo', path=self.srcpath)
        child = ('export:\n  build: bfg9000\n  linkage:\n' +
                 '    type: pkg_config\n    unknown: blah')
        loc = 'line 5, column 5'
        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock_open_data(child)), \
             assert_logging([('fetch', 'foo from {}'.format(self.srcpath))]), \
             self.assertRaisesRegex(YamlParseError, loc):
            pkg.fetch(self.metadata, self.config)

    def test_infer_build_invalid_parent_linkage(self):
        child = 'export:\n  build: bfg9000'

        linkage = yaml.load('unknown', Loader=SafeLineLoader)
        pkg = self.make_package('foo', path=self.srcpath, linkage=linkage)
        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock_open_data(child)), \
             assert_logging([('fetch', 'foo from {}'.format(self.srcpath))]), \
             self.assertRaises(FieldError):
            pkg.fetch(self.metadata, self.config)

        linkage = yaml.load('type: pkg_config\nunknown: blah',
                            Loader=SafeLineLoader)
        pkg = self.make_package('foo', path=self.srcpath, linkage=linkage)
        loc = 'line 2, column 1'
        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock_open_data(child)), \
             assert_logging([('fetch', 'foo from {}'.format(self.srcpath))]), \
             self.assertRaisesRegex(YamlParseError, loc):
            pkg.fetch(self.metadata, self.config)

    def test_linkage(self):
        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                linkage='pkg_config')
        builder = self.make_builder(Bfg9000Builder, pkg)
        self.assertEqual(pkg.path, Path(self.srcpath))
        self.assertEqual(pkg.builders, [builder])

        with assert_logging([('fetch', 'foo from {}'.format(self.srcpath))]):
            pkg.fetch(self.metadata, self.config)
        self.check_resolve(pkg)

        with mock.patch('subprocess.run') as mrun:
            pkg.version(self.metadata)
            mrun.assert_called_once_with(
                ['pkg-config', 'foo', '--modversion'],
                check=True, env={'PKG_CONFIG_PATH': self.pkgconfdir('foo')},
                stdout=subprocess.PIPE, universal_newlines=True
            )

        linkage = {'type': 'pkg_config', 'pkg_config_path': 'pkgconf'}
        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                linkage=linkage)
        self.assertEqual(pkg.path, Path(self.srcpath))
        self.assertEqual(pkg.builders, [builder])

        with assert_logging([('fetch', 'foo from {}'.format(self.srcpath))]):
            pkg.fetch(self.metadata, self.config)
        self.check_resolve(pkg, linkage={
            'name': 'foo', 'type': 'pkg_config', 'pcnames': ['foo'],
            'pkg_config_path': [self.pkgconfdir('foo', 'pkgconf')],
        })

        linkage = {'type': 'path', 'libraries': []}
        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                linkage=linkage)
        self.assertEqual(pkg.path, Path(self.srcpath))
        self.assertEqual(pkg.builders, [builder])

        with assert_logging([('fetch', 'foo from {}'.format(self.srcpath))]):
            pkg.fetch(self.metadata, self.config)
        self.check_resolve(pkg, linkage={
            'name': 'foo', 'type': 'path', 'generated': True,
            'auto_link': False, 'pcnames': ['foo'],
            'pkg_config_path': [self.pkgconfdir(None)],
        })

        with mock.patch('subprocess.run') as mrun:
            self.assertEqual(pkg.version(self.metadata), None)
            mrun.assert_not_called()

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                submodules=submodules_required)
        self.check_resolve(pkg, submodules=['sub'])

        pkg = self.make_package(
            'foo', path=self.srcpath, build='bfg9000',
            linkage={'type': 'pkg_config', 'pcname': 'bar'},
            submodules=submodules_required
        )
        self.check_resolve(pkg, submodules=['sub'], linkage={
            'name': 'foo[sub]', 'type': 'pkg_config',
            'pcnames': ['bar', 'foo_sub'],
            'pkg_config_path': [self.pkgconfdir('foo')],
        })

        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                submodules=submodules_optional)
        self.check_resolve(pkg, submodules=['sub'])

        pkg = self.make_package(
            'foo', path=self.srcpath, build='bfg9000',
            linkage={'type': 'pkg_config', 'pcname': 'bar'},
            submodules=submodules_optional
        )
        self.check_resolve(pkg, submodules=['sub'], linkage={
            'name': 'foo[sub]', 'type': 'pkg_config',
            'pcnames': ['bar', 'foo_sub'],
            'pkg_config_path': [self.pkgconfdir('foo')],
        })

    def test_invalid_submodule(self):
        pkg = self.make_package(
            'foo', path=self.srcpath, build='bfg9000',
            submodules={'names': ['sub'], 'required': True}
        )
        with self.assertRaises(ValueError):
            pkg.get_linkage(self.metadata, ['invalid'])

    def test_deploy(self):
        deploy_dirs = {'prefix': '/usr/local'}
        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                deploy_dirs=deploy_dirs)
        self.assertEqual(pkg.should_deploy, True)

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('subprocess.run') as mrun:
            with assert_logging([('resolve', 'foo')]):
                pkg.resolve(self.metadata)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'foo.log'
            ), 'a')
            builddir = os.path.join(self.pkgdir, 'build', 'foo')
            mrun.assert_any_call(
                ['bfg9000', 'configure', builddir, '--prefix', '/usr/local'],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, check=True, env={}
            )

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('subprocess.run'):
            with assert_logging([('deploy', 'foo')]):
                pkg.deploy(self.metadata)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'deploy', 'foo.log'
            ), 'a')

        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                deploy=False)
        self.assertEqual(pkg.should_deploy, False)

        with mock_open_log() as mopen:
            pkg.deploy(self.metadata)
            mopen.assert_not_called()

    def test_clean_pre(self):
        oldpkg = self.make_package('foo', path=self.srcpath, build='bfg9000')
        newpkg = self.make_package(AptPackage, 'foo')

        # System -> Apt
        self.assertEqual(oldpkg.clean_pre(self.metadata, newpkg), False)

        # Apt -> nothing
        self.assertEqual(oldpkg.clean_pre(self.metadata, None), False)

    def test_clean_post(self):
        otherpath = os.path.join(test_data_dir, 'other_project')
        oldpkg = self.make_package('foo', path=self.srcpath, build='bfg9000')
        newpkg1 = self.make_package('foo', path=otherpath, build='bfg9000')
        newpkg2 = self.make_package(AptPackage, 'foo')

        # Directory -> Directory (same)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:
            self.assertEqual(oldpkg.clean_post(self.metadata, oldpkg), False)
            mlog.assert_not_called()
            mclean.assert_not_called()

        # Directory -> Directory (different)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:
            self.assertEqual(oldpkg.clean_post(self.metadata, newpkg1), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.metadata, oldpkg)

        # Directory -> Apt
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:
            self.assertEqual(oldpkg.clean_post(self.metadata, newpkg2), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.metadata, oldpkg)

        # Directory -> nothing
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:
            self.assertEqual(oldpkg.clean_post(self.metadata, None), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.metadata, oldpkg)

        # Directory -> nothing (quiet)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:
            self.assertEqual(oldpkg.clean_post(self.metadata, None, True),
                             True)
            mlog.assert_not_called()
            mclean.assert_called_once_with(self.metadata, oldpkg)

    def test_clean_all(self):
        otherpath = os.path.join(test_data_dir, 'other_project')
        oldpkg = self.make_package('foo', path=self.srcpath, build='bfg9000')
        newpkg1 = self.make_package('foo', path=otherpath, build='bfg9000')
        newpkg2 = self.make_package(AptPackage, 'foo')

        # Directory -> Directory (same)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:
            self.assertEqual(oldpkg.clean_all(self.metadata, oldpkg),
                             (False, False))
            mlog.assert_not_called()
            mclean.assert_not_called()

        # Directory -> Directory (different)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:
            self.assertEqual(oldpkg.clean_all(self.metadata, newpkg1),
                             (False, True))
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.metadata, oldpkg)

        # Directory -> Apt
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:
            self.assertEqual(oldpkg.clean_all(self.metadata, newpkg2),
                             (False, True))
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.metadata, oldpkg)

        # Directory -> nothing
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:
            self.assertEqual(oldpkg.clean_all(self.metadata, None),
                             (False, True))
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.metadata, oldpkg)

    def test_equality(self):
        otherpath = os.path.join(test_data_dir, 'other_project')
        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000')

        self.assertEqual(pkg, self.make_package(
            'foo', path=self.srcpath, build='bfg9000'
        ))
        self.assertEqual(pkg, self.make_package(
            'foo', path=self.srcpath, build='bfg9000'
        ))

        self.assertNotEqual(pkg, self.make_package(
            'bar', path=self.srcpath, build='bfg9000'
        ))
        self.assertNotEqual(pkg, self.make_package(
            'foo', path=otherpath, build='bfg9000'
        ))

    def test_rehydrate(self):
        opts = self.make_options()
        pkg = DirectoryPackage('foo', path=self.srcpath, build='bfg9000',
                               _options=opts, config_file=self.config_file)
        data = through_json(pkg.dehydrate())
        self.assertNotIn('pending_linkage', data)
        self.assertEqual(pkg, Package.rehydrate(data, _options=opts))

        pkg = DirectoryPackage('foo', path=self.srcpath, _options=opts,
                               config_file=self.config_file)
        with self.assertRaises(ConfigurationError):
            data = pkg.dehydrate()

    def test_upgrade(self):
        opts = self.make_options()
        data = {
            'origin': 'directory', '_version': 0, 'name': 'foo',
            'path': {'base': 'cfgdir', 'path': '.'},
            'builder': {'type': 'none', '_version': 1, 'name': 'foo'},
            'linkage': {'type': 'system', '_version': 1},
        }
        with mock.patch.object(DirectoryPackage, 'upgrade',
                               side_effect=DirectoryPackage.upgrade) as m:
            pkg = Package.rehydrate(data, _options=opts)
            self.assertIsInstance(pkg, DirectoryPackage)
            self.assertIsInstance(pkg.linkage, SystemLinkage)
            self.assertEqual([type(i) for i in pkg.builders], [NoneBuilder])
            m.assert_called_once()

    def test_builder_types(self):
        pkg = DirectoryPackage('foo', path=self.srcpath, build='bfg9000',
                               _options=self.make_options(),
                               config_file=self.config_file)
        self.assertEqual(pkg.builder_types, ['bfg9000'])

        pkg = DirectoryPackage('foo', path=self.srcpath,
                               _options=self.make_options(),
                               config_file=self.config_file)
        with self.assertRaises(ConfigurationError):
            pkg.builder_types
