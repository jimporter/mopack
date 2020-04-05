from unittest import mock, TestCase

from .. import mock_open_log

from mopack.sources.apt import AptPackage


class TestApt(TestCase):
    def test_basic(self):
        pkg = AptPackage('foo', _config_file='/path/to/mopack.yml')
        self.assertEqual(pkg.remote, 'libfoo-dev')

        with mock_open_log() as mo, \
             mock.patch('subprocess.check_call') as mc:  # noqa
            AptPackage.fetch_all('/path/to/builddir/mopack', [pkg])
            mo.assert_called_with('/path/to/builddir/mopack/apt.log', 'w')
            mc.assert_called_with(['sudo', 'apt-get', 'install', '-y',
                                   'libfoo-dev'],
                                  stdout=mo(), stderr=mo())

    def test_remote(self):
        pkg = AptPackage('foo', remote='foo-dev',
                         _config_file='/path/to/mopack.yml')
        self.assertEqual(pkg.remote, 'foo-dev')

        with mock_open_log() as mo, \
             mock.patch('subprocess.check_call') as mc:  # noqa
            AptPackage.fetch_all('/path/to/builddir/mopack', [pkg])
            mo.assert_called_with('/path/to/builddir/mopack/apt.log', 'w')
            mc.assert_called_with(['sudo', 'apt-get', 'install', '-y',
                                   'foo-dev'],
                                  stdout=mo(), stderr=mo())

    def test_multiple(self):
        pkg1 = AptPackage('foo', _config_file='/path/to/mopack.yml')
        pkg2 = AptPackage('bar', remote='bar-dev',
                          _config_file='/path/to/mopack.yml')

        with mock_open_log() as mo, \
             mock.patch('subprocess.check_call') as mc:  # noqa
            AptPackage.fetch_all('/path/to/builddir/mopack', [pkg1, pkg2])
            mo.assert_called_with('/path/to/builddir/mopack/apt.log', 'w')
            mc.assert_called_with(['sudo', 'apt-get', 'install', '-y',
                                   'libfoo-dev', 'bar-dev'],
                                  stdout=mo(), stderr=mo())
