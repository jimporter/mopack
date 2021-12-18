import json
from unittest import mock, TestCase

from . import Stream

from mopack.metadata import Metadata, MetadataVersionError
from mopack.sources.apt import AptPackage
from mopack.sources.system import SystemPackage


class TestMetadata(TestCase):
    config_file = '/path/to/mopack.yml'

    def test_get_package(self):
        metadata = Metadata()
        pkg = AptPackage('foo', _options=metadata.options,
                         config_file=self.config_file)
        pkg.resolved = True
        metadata.add_package(pkg)
        self.assertIs(metadata.get_package('foo'), pkg)

    def test_get_package_fallback(self):
        metadata = Metadata()
        self.assertEqual(
            metadata.get_package('foo'),
            SystemPackage('foo', _options=metadata.options,
                          config_file=self.config_file)
        )

    def test_get_package_unresolved(self):
        metadata = Metadata()
        pkg = AptPackage('foo', _options=metadata.options,
                         config_file=self.config_file)
        metadata.add_package(pkg)
        with self.assertRaises(ValueError):
            metadata.get_package('foo')

    def test_get_package_strict(self):
        metadata = Metadata()
        with self.assertRaises(ValueError):
            metadata.get_package('foo', strict=True)

    def test_save(self):
        out = Stream('')
        with mock.patch('os.makedirs'), \
             mock.patch('builtins.open', return_value=out):
            metadata = Metadata()
            pkg = AptPackage('foo', _options=metadata.options,
                             config_file=self.config_file)
            pkg.resolved = True
            metadata.add_package(pkg)
            metadata.save(self.config_file)

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
                Metadata.load(self.config_file)
