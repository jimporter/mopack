from . import MockPackage, LinkageTest

from mopack.types import FieldError
from mopack.linkages import make_linkage
from mopack.linkages.pkg_config import PkgConfigLinkage
from mopack.path import Path


class TestMakeLinkage(LinkageTest):
    path_bases = ('srcdir', 'builddir')

    def setUp(self):
        self.pkg = MockPackage(
            'foo', srcdir=self.srcdir, builddir=self.builddir,
            _options=self.make_options()
        )

    def test_make(self):
        linkage = make_linkage(self.pkg, {'type': 'pkg_config',
                                          'pkg_config_path': 'path'})
        self.assertIsInstance(linkage, PkgConfigLinkage)
        self.assertEqual(linkage.pkg_config_path, [Path('path', 'builddir')])

    def test_make_string(self):
        linkage = make_linkage(self.pkg, 'pkg_config')
        self.assertIsInstance(linkage, PkgConfigLinkage)
        self.assertEqual(linkage.pkg_config_path,
                         [Path('pkgconfig', 'builddir')])

    def test_unknown_linkage(self):
        with self.assertRaises(FieldError):
            make_linkage(self.pkg, {'type': 'goofy'})

    def test_no_linkage(self):
        with self.assertRaises(TypeError):
            make_linkage(self.pkg, None)

    def test_invalid_keys(self):
        with self.assertRaises(TypeError):
            make_linkage(self.pkg, {'type': 'pkg_config', 'unknown': 'blah'})

    def test_invalid_values(self):
        with self.assertRaises(FieldError):
            make_linkage(self.pkg, {'type': 'pkg_config',
                                    'pkg_config_path': '..'})
