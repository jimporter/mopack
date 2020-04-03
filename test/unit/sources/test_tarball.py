import unittest

from mopack.sources.tarball import TarballPackage


class TestTarball(unittest.TestCase):
    def test_url(self):
        p = TarballPackage('foo', build='bfg9000', url='http://example.com')
        self.assertEqual(p.url, 'http://example.com')
        self.assertEqual(p.path, None)

    def test_path(self):
        p = TarballPackage('foo', build='bfg9000', path='/path/to/file.tar.gz')
        self.assertEqual(p.url, None)
        self.assertEqual(p.path, '/path/to/file.tar.gz')

    def test_missing_url_path(self):
        with self.assertRaises(TypeError):
            TarballPackage('foo', build='bfg9000')
