import os
import yaml

from . import *
from .... import *

from mopack.builders.bfg9000 import Bfg9000Builder
from mopack.config import Config
from mopack.path import Path
from mopack.sources import Package
from mopack.sources.apt import AptPackage
from mopack.sources.sdist import DirectoryPackage
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
        self.config = Config([])

    def test_resolve(self):
        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000')
        self.assertEqual(pkg.path, Path('absolute', self.srcpath))
        self.assertEqual(pkg.builder, self.make_builder(Bfg9000Builder, 'foo'))
        self.assertEqual(pkg.should_deploy, True)

        pkg.fetch(self.pkgdir, self.config)
        self.check_resolve(pkg)

    def test_build(self):
        build = {'type': 'bfg9000', 'extra_args': '--extra'}
        pkg = self.make_package('foo', path=self.srcpath, build=build,
                                usage='pkg-config')
        self.assertEqual(pkg.path, Path('absolute', self.srcpath))
        self.assertEqual(pkg.builder, self.make_builder(
            Bfg9000Builder, 'foo', extra_args='--extra'
        ))
        self.assertEqual(pkg.should_deploy, True)

        pkg.fetch(self.pkgdir, self.config)
        self.check_resolve(pkg)

    def test_infer_build(self):
        mock_open = mock.mock_open(read_data='export:\n  build: bfg9000')

        pkg = self.make_package('foo', path=self.srcpath)
        self.assertEqual(pkg.builder, None)

        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock_open):  # noqa
            config = pkg.fetch(self.pkgdir, self.config)
            self.assertEqual(config.export.build, 'bfg9000')
            self.assertEqual(pkg.builder, self.make_builder(
                Bfg9000Builder, 'foo'
            ))
        self.check_resolve(pkg)

        pkg = self.make_package('foo', path=self.srcpath,
                                usage={'type': 'system'})

        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock_open):  # noqa
            config = pkg.fetch(self.pkgdir, self.config)
            self.assertEqual(config.export.build, 'bfg9000')
            self.assertEqual(pkg.builder, self.make_builder(
                Bfg9000Builder, 'foo', usage={'type': 'system'}
            ))
        with mock.patch('subprocess.run', side_effect=OSError()):
            self.check_resolve(pkg, usage={
                'type': 'path', 'auto_link': False, 'include_path': [],
                'library_path': [], 'headers': [], 'libraries': ['foo'],
                'compile_flags': [], 'link_flags': [],
            })

    def test_infer_submodules(self):
        data = 'export:\n  submodules: [french, english]\n  build: bfg9000'
        mock_open = mock.mock_open(read_data=data)

        srcpath = os.path.join(test_data_dir, 'hello-multi-bfg')
        pkg = self.make_package('foo', path=srcpath)
        self.assertEqual(pkg.builder, None)

        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock_open):  # noqa
            config = pkg.fetch(self.pkgdir, self.config)
            self.assertEqual(config.export.build, 'bfg9000')
            self.assertEqual(config.export.submodules,
                             ['french', 'english'])
            self.assertEqual(pkg.builder, self.make_builder(
                Bfg9000Builder, 'foo', submodules={
                    'names': ['french', 'english'], 'required': True
                }
            ))
        self.check_resolve(pkg, submodules=['french'])

        pkg = self.make_package('foo', path=srcpath, submodules=['sub'])
        self.assertEqual(pkg.builder, None)

        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock_open):  # noqa
            config = pkg.fetch(self.pkgdir, self.config)
            self.assertEqual(config.export.build, 'bfg9000')
            self.assertEqual(config.export.submodules,
                             ['french', 'english'])
            self.assertEqual(pkg.builder, self.make_builder(
                Bfg9000Builder, 'foo', submodules={
                    'names': ['sub'], 'required': True
                }
            ))
        self.check_resolve(pkg, submodules=['sub'])

    def test_infer_build_invalid(self):
        pkg = self.make_package('foo', path=self.srcpath)

        child = ''
        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock.mock_open(read_data=child)), \
             self.assertRaises(ConfigurationError):  # noqa
            pkg.fetch(self.pkgdir, self.config)

        child = 'export:\n  build: unknown'
        loc = 'line 2, column 10'
        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock.mock_open(read_data=child)), \
             self.assertRaisesRegex(YamlParseError, loc):  # noqa
            pkg.fetch(self.pkgdir, self.config)

        child = 'export:\n  build:\n    type: bfg9000\n    unknown: blah'
        loc = 'line 4, column 5'
        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock.mock_open(read_data=child)), \
             self.assertRaisesRegex(YamlParseError, loc):  # noqa
            pkg.fetch(self.pkgdir, self.config)

        child = 'export:\n  build: bfg9000\n  usage: unknown'
        loc = 'line 3, column 10'
        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock.mock_open(read_data=child)), \
             self.assertRaises(YamlParseError):  # noqa
            pkg.fetch(self.pkgdir, self.config)

        child = ('export:\n  build: bfg9000\n  usage:\n' +
                 '    type: pkg-config\n    unknown: blah')
        loc = 'line 5, column 5'
        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock.mock_open(read_data=child)), \
             self.assertRaisesRegex(YamlParseError, loc):  # noqa
            pkg.fetch(self.pkgdir, self.config)

    def test_infer_build_invalid_parent_usage(self):
        child = 'export:\n  build: bfg9000'

        usage = yaml.load('unknown', Loader=SafeLineLoader)
        pkg = self.make_package('foo', path=self.srcpath, usage=usage)
        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock.mock_open(read_data=child)), \
             self.assertRaises(FieldError):  # noqa
            pkg.fetch(self.pkgdir, self.config)

        usage = yaml.load('type: pkg-config\nunknown: blah',
                          Loader=SafeLineLoader)
        pkg = self.make_package('foo', path=self.srcpath, usage=usage)
        loc = 'line 2, column 1'
        with mock.patch('os.path.isdir', mock_isdir), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('builtins.open', mock.mock_open(read_data=child)), \
             self.assertRaisesRegex(YamlParseError, loc):  # noqa
            pkg.fetch(self.pkgdir, self.config)

    def test_usage(self):
        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                usage='pkg-config')
        self.assertEqual(pkg.path, Path('absolute', self.srcpath))
        self.assertEqual(pkg.builder, self.make_builder(
            Bfg9000Builder, 'foo', usage='pkg-config'
        ))

        pkg.fetch(self.pkgdir, self.config)
        self.check_resolve(pkg)

        usage = {'type': 'pkg-config', 'path': 'pkgconf'}
        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                usage=usage)
        self.assertEqual(pkg.path, Path('absolute', self.srcpath))
        self.assertEqual(pkg.builder, self.make_builder(
            Bfg9000Builder, 'foo', usage=usage
        ))

        pkg.fetch(self.pkgdir, self.config)
        self.check_resolve(pkg, usage={
            'type': 'pkg-config', 'path': self.pkgconfdir('foo', 'pkgconf'),
            'pcfiles': ['foo'], 'extra_args': [],
        })

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                submodules=submodules_required)
        self.check_resolve(pkg, submodules=['sub'])

        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                usage={'type': 'pkg-config', 'pcfile': 'bar'},
                                submodules=submodules_required)
        self.check_resolve(pkg, submodules=['sub'], usage={
            'type': 'pkg-config', 'path': self.pkgconfdir('foo'),
            'pcfiles': ['bar', 'foo_sub'], 'extra_args': [],
        })

        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                submodules=submodules_optional)
        self.check_resolve(pkg, submodules=['sub'])

        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                usage={'type': 'pkg-config', 'pcfile': 'bar'},
                                submodules=submodules_optional)
        self.check_resolve(pkg, submodules=['sub'], usage={
            'type': 'pkg-config', 'path': self.pkgconfdir('foo'),
            'pcfiles': ['bar', 'foo_sub'], 'extra_args': [],
        })

    def test_invalid_submodule(self):
        pkg = self.make_package(
            'foo', path=self.srcpath, build='bfg9000',
            submodules={'names': ['sub'], 'required': True}
        )
        with self.assertRaises(ValueError):
            pkg.get_usage(self.pkgdir, ['invalid'])

    def test_deploy(self):
        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000')
        self.assertEqual(pkg.should_deploy, True)

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('subprocess.run'):  # noqa
            pkg.deploy(self.pkgdir)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'deploy', 'foo.log'
            ), 'a')

        pkg = self.make_package('foo', path=self.srcpath, build='bfg9000',
                                deploy=False)
        self.assertEqual(pkg.should_deploy, False)

        with mock_open_log() as mopen:
            pkg.deploy(self.pkgdir)
            mopen.assert_not_called()

    def test_clean_pre(self):
        oldpkg = self.make_package('foo', path=self.srcpath, build='bfg9000')
        newpkg = self.make_package(AptPackage, 'foo')

        # System -> Apt
        self.assertEqual(oldpkg.clean_pre(self.pkgdir, newpkg), False)

        # Apt -> nothing
        self.assertEqual(oldpkg.clean_pre(self.pkgdir, None), False)

    def test_clean_post(self):
        otherpath = os.path.join(test_data_dir, 'other_project')
        oldpkg = self.make_package('foo', path=self.srcpath, build='bfg9000')
        newpkg1 = self.make_package('foo', path=otherpath, build='bfg9000')
        newpkg2 = self.make_package(AptPackage, 'foo')

        # Directory -> Directory (same)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, oldpkg), False)
            mlog.assert_not_called()
            mclean.assert_not_called()

        # Directory -> Directory (different)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, newpkg1), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)

        # Directory -> Apt
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, newpkg2), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)

        # Directory -> nothing
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, None), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)

        # Directory -> nothing (quiet)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_post(self.pkgdir, None, True), True)
            mlog.assert_not_called()
            mclean.assert_called_once_with(self.pkgdir)

    def test_clean_all(self):
        otherpath = os.path.join(test_data_dir, 'other_project')
        oldpkg = self.make_package('foo', path=self.srcpath, build='bfg9000')
        newpkg1 = self.make_package('foo', path=otherpath, build='bfg9000')
        newpkg2 = self.make_package(AptPackage, 'foo')

        # Directory -> Directory (same)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, oldpkg),
                             (False, False))
            mlog.assert_not_called()
            mclean.assert_not_called()

        # Directory -> Directory (different)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, newpkg1),
                             (False, True))
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)

        # Directory -> Apt
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, newpkg2),
                             (False, True))
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)

        # Directory -> nothing
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:  # noqa
            self.assertEqual(oldpkg.clean_all(self.pkgdir, None),
                             (False, True))
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.pkgdir)

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
        data = pkg.dehydrate()
        self.assertNotIn('pending_usage', data)
        self.assertEqual(pkg, Package.rehydrate(data, _options=opts))

        pkg = DirectoryPackage('foo', path=self.srcpath, _options=opts,
                               config_file=self.config_file)
        with self.assertRaises(ConfigurationError):
            data = pkg.dehydrate()

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