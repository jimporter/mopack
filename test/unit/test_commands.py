import json
import os
from unittest import mock, TestCase
from textwrap import dedent

from . import mock_open_data, Stream

from mopack import commands
from mopack.config import Config
from mopack.sources.apt import AptPackage
from mopack.sources.sdist import DirectoryPackage
from mopack.sources.system import SystemPackage


class TestMetadata(TestCase):
    config_file = '/path/to/mopack.yml'

    def test_get_package(self):
        metadata = commands.Metadata()
        pkg = AptPackage('foo', _options=metadata.options,
                         config_file=self.config_file)
        pkg.resolved = True
        metadata.add_package(pkg)
        self.assertIs(metadata.get_package('foo'), pkg)

    def test_get_package_fallback(self):
        metadata = commands.Metadata()
        self.assertEqual(
            metadata.get_package('foo'),
            SystemPackage('foo', _options=metadata.options,
                          config_file=self.config_file)
        )

    def test_get_package_unresolved(self):
        metadata = commands.Metadata()
        pkg = AptPackage('foo', _options=metadata.options,
                         config_file=self.config_file)
        metadata.add_package(pkg)
        with self.assertRaises(ValueError):
            metadata.get_package('foo')

    def test_get_package_strict(self):
        metadata = commands.Metadata()
        with self.assertRaises(ValueError):
            metadata.get_package('foo', strict=True)

    def test_save(self):
        out = Stream('')
        with mock.patch('os.makedirs'), \
             mock.patch('builtins.open', return_value=out):
            metadata = commands.Metadata()
            pkg = AptPackage('foo', _options=metadata.options,
                             config_file=self.config_file)
            pkg.resolved = True
            metadata.add_package(pkg)
            metadata.save(self.config_file)

        # Test round-tripping a package.
        with mock.patch('builtins.open',
                        mock.mock_open(read_data=out.getvalue())):
            metadata_copy = commands.Metadata.load(self.config_file)
            self.assertEqual(metadata_copy.get_package('foo'), pkg)

    def test_load_invalid_version(self):
        data = {
            'version': 99,
            'config_files': {'explicit': [], 'implicit': []},
            'metadata': {'options': {}, 'packages': {}},
        }
        with mock.patch('builtins.open',
                        mock.mock_open(read_data=json.dumps(data))):
            with self.assertRaises(commands.MetadataVersionError):
                commands.Metadata.load(self.config_file)


class CommandsTestCase(TestCase):
    pkgdir = os.path.abspath('/path/to/builddir/mopack')

    def make_empty_config(self, files=[]):
        with mock.patch('builtins.open', mock_open_data('')):
            return Config(files)

    def make_apt_config(self):
        cfg_data = dedent("""\
          packages:
            foo:
              source: apt
              remote: libfoo1-dev
        """)
        with mock.patch('builtins.open', mock_open_data(cfg_data)):
            return Config(['mopack.yml'])


class TestFetch(CommandsTestCase):
    def test_empty(self):
        cfg = self.make_empty_config()
        with mock.patch('os.path.exists', return_value=False), \
             mock.patch('builtins.open',
                        side_effect=FileNotFoundError()):  # noqa
            metadata = commands.fetch(cfg, self.pkgdir)
            self.assertEqual(metadata.files, [])
            self.assertEqual(metadata.implicit_files, [])
            self.assertEqual(metadata.packages, {})

    def test_binary_package(self):
        cfg = self.make_apt_config()
        with mock.patch('os.path.exists', return_value=False), \
             mock.patch('builtins.open', side_effect=FileNotFoundError()), \
             mock.patch.object(AptPackage, 'fetch') as mfetch:  # noqa
            metadata = commands.fetch(cfg, self.pkgdir)
            self.assertEqual(metadata.files, [os.path.abspath('mopack.yml')])
            self.assertEqual(metadata.implicit_files, [])
            self.assertEqual(metadata.packages, {'foo': AptPackage(
                'foo', remote='libfoo1-dev', _options=cfg.options,
                config_file=os.path.abspath('mopack.yml'),
            )})
            mfetch.assert_called_once()

    def test_removed_package(self):
        cfg = self.make_empty_config()

        old_metadata = commands.Metadata()
        old_metadata.add_package(AptPackage(
            'foo', _options=cfg.options,
            config_file=os.path.abspath('mopack.yml'),
        ))

        with mock.patch('os.path.exists', return_value=False), \
             mock.patch('mopack.commands.Metadata.try_load',
                        return_value=old_metadata), \
             mock.patch.object(AptPackage, 'clean_all') as mclean:
            metadata = commands.fetch(cfg, self.pkgdir)
            self.assertEqual(metadata.files, [])
            self.assertEqual(metadata.implicit_files, [])
            self.assertEqual(metadata.packages, {})
            mclean.assert_called_once()

    def test_changed_package(self):
        cfg = self.make_apt_config()

        old_metadata = commands.Metadata()
        old_metadata.add_package(AptPackage(
            'foo', _options=cfg.options,
            config_file=os.path.abspath('mopack.yml'),
        ))

        with mock.patch('os.path.exists', return_value=False), \
             mock.patch('mopack.commands.Metadata.try_load',
                        return_value=old_metadata), \
             mock.patch.object(AptPackage, 'fetch') as mfetch, \
             mock.patch.object(AptPackage, 'clean_post') as mclean:  # noqa
            metadata = commands.fetch(cfg, self.pkgdir)
            self.assertEqual(metadata.files, [os.path.abspath('mopack.yml')])
            self.assertEqual(metadata.implicit_files, [])
            self.assertEqual(metadata.packages, {'foo': AptPackage(
                'foo', remote='libfoo1-dev', _options=cfg.options,
                config_file=os.path.abspath('mopack.yml'),
            )})
            mfetch.assert_called_once()
            mclean.assert_called_once()


class TestResolve(CommandsTestCase):
    def test_empty(self):
        with mock.patch('mopack.log.info') as mlog, \
             mock.patch.object(commands.Metadata, 'save') as msave:  # noqa
            commands.resolve(self.make_empty_config(), self.pkgdir)
            mlog.assert_called_once_with('no inputs')
            msave.assert_not_called()

    def test_package(self):
        cfg = self.make_empty_config(['mopack.yml'])

        metadata = commands.Metadata()
        metadata.add_package(DirectoryPackage(
            'foo', path='path', build='none', usage='pkg_config',
            _options=cfg.options,
            config_file=os.path.abspath('mopack.yml'),
        ))

        with mock.patch('mopack.commands.fetch', return_value=metadata), \
             mock.patch.object(DirectoryPackage, 'resolve') as mresolve, \
             mock.patch.object(commands.Metadata, 'save') as msave:  # noqa
            commands.resolve(cfg, self.pkgdir)
            mresolve.assert_called_once()
            self.assertEqual(msave.call_count, 2)

    def test_package_no_deps(self):
        cfg = self.make_empty_config(['mopack.yml'])

        metadata = commands.Metadata()
        metadata.add_package(DirectoryPackage(
            'foo', path='path', build='none', usage='pkg_config',
            _options=cfg.options,
            config_file=os.path.abspath('mopack.yml'),
        ))

        with mock.patch('mopack.commands.fetch', return_value=metadata), \
             mock.patch.object(DirectoryPackage, 'needs_dependencies',
                               False), \
             mock.patch.object(DirectoryPackage, 'resolve') as mresolve, \
             mock.patch.object(commands.Metadata, 'save') as msave:  # noqa
            commands.resolve(cfg, self.pkgdir)
            mresolve.assert_called_once()
            msave.assert_called_once()

    def test_package_failure(self):
        cfg = self.make_empty_config(['mopack.yml'])

        metadata = commands.Metadata()
        metadata.add_package(DirectoryPackage(
            'foo', path='path', build='none', usage='pkg_config',
            _options=cfg.options,
            config_file=os.path.abspath('mopack.yml'),
        ))

        with mock.patch('mopack.commands.fetch', return_value=metadata), \
             mock.patch.object(DirectoryPackage, 'resolve',
                               side_effect=RuntimeError()) as mresolve, \
             mock.patch.object(DirectoryPackage, 'clean_post') as mclean, \
             mock.patch.object(commands.Metadata, 'save') as msave:  # noqa
            with self.assertRaises(RuntimeError):
                commands.resolve(cfg, self.pkgdir)
            mresolve.assert_called_once()
            mclean.assert_called_once()
            self.assertEqual(msave.call_count, 2)

    def test_batch_package(self):
        cfg = self.make_empty_config(['mopack.yml'])

        metadata = commands.Metadata()
        metadata.add_package(AptPackage(
            'foo', _options=cfg.options,
            config_file=os.path.abspath('mopack.yml'),
        ))

        with mock.patch('mopack.commands.fetch', return_value=metadata), \
             mock.patch.object(AptPackage, 'resolve_all') as mresolve, \
             mock.patch.object(commands.Metadata, 'save') as msave:  # noqa
            commands.resolve(cfg, self.pkgdir)
            mresolve.assert_called_once()
            msave.assert_called_once()

    def test_batch_package_failure(self):
        cfg = self.make_empty_config(['mopack.yml'])

        metadata = commands.Metadata()
        metadata.add_package(AptPackage(
            'foo', _options=cfg.options,
            config_file=os.path.abspath('mopack.yml'),
        ))

        with mock.patch('mopack.commands.fetch', return_value=metadata), \
             mock.patch.object(AptPackage, 'resolve_all',
                               side_effect=RuntimeError()) as mresolve, \
             mock.patch.object(AptPackage, 'clean_post') as mclean, \
             mock.patch.object(commands.Metadata, 'save') as msave:  # noqa
            with self.assertRaises(RuntimeError):
                commands.resolve(cfg, self.pkgdir)
            mresolve.assert_called_once()
            mclean.assert_called_once()
            msave.assert_called_once()
