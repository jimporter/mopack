import json
import os
from unittest import mock

from . import OptionsTest, Stream
from .. import test_data_dir

from mopack.metadata import Metadata, MetadataVersionError
from mopack.origins.apt import AptPackage
from mopack.origins.conan import ConanPackage
from mopack.origins.system import SystemPackage


class TestMetadata(OptionsTest):
    pkgdir = '/path/to/builddir/mopack'
    config_file = '/path/to/mopack.yml'

    def test_get_package(self):
        metadata = Metadata(self.pkgdir)
        pkg = AptPackage('foo', _options=metadata.options,
                         config_file=self.config_file)
        pkg.resolved = True
        metadata.add_package(pkg)
        self.assertIs(metadata.get_package('foo'), pkg)

    def test_get_package_fallback(self):
        metadata = Metadata(self.pkgdir)
        self.assertEqual(
            metadata.get_package('foo'),
            SystemPackage('foo', _options=metadata.options,
                          config_file=self.config_file)
        )

    def test_get_package_unresolved(self):
        metadata = Metadata(self.pkgdir)
        pkg = AptPackage('foo', _options=metadata.options,
                         config_file=self.config_file)
        metadata.add_package(pkg)
        with self.assertRaises(ValueError):
            metadata.get_package('foo')

    def test_get_package_strict(self):
        metadata = Metadata(self.pkgdir, self.make_options({'strict': True}))
        with self.assertRaises(KeyError):
            metadata.get_package('foo')

    def test_save(self):
        out = Stream('')
        with mock.patch('os.makedirs'), \
             mock.patch('builtins.open', return_value=out):
            metadata = Metadata(self.pkgdir)
            pkg = AptPackage('foo', _options=metadata.options,
                             config_file=self.config_file)
            pkg.resolved = True
            metadata.add_package(pkg)
            metadata.save()

        # Test round-tripping a package.
        with mock.patch('builtins.open',
                        mock.mock_open(read_data=out.getvalue())):
            metadata_copy = Metadata.load(self.config_file)
            self.assertEqual(metadata_copy.get_package('foo'), pkg)

    def test_load_invalid_version(self):
        data = {
            'version': 99,
            'config_files': {'explicit': [], 'implicit': []},
            'metadata': {'options': {}, 'packages': {}},
        }
        with mock.patch('builtins.open',
                        mock.mock_open(read_data=json.dumps(data))):
            with self.assertRaises(MetadataVersionError):
                Metadata.load(self.pkgdir)

    def test_upgrade_from_v1(self):
        metadata = Metadata.load(os.path.join(test_data_dir, 'metadata', 'v1'))
        self.assertIsInstance(metadata.get_package('zlib'), ConanPackage)
        self.assertEqual(metadata.options.common.expr_symbols,
                         {'host_platform': mock.ANY,
                          'target_platform': 'linux',
                          'env': {},
                          'deploy_dirs': {}})
