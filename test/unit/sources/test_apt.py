import os
from unittest import mock, TestCase

from .. import mock_open_log
from ... import *

from mopack.sources.apt import AptPackage


class TestApt(TestCase):
    def test_basic(self):
        pkg = AptPackage('foo', _config_file='/path/to/mopack.yml')
        self.assertEqual(pkg.depends, ['foo'])

        with mock_open_log() as mo, \
             mock.patch('subprocess.check_call') as mc:  # noqa
            AptPackage.fetch_all('/path/to/builddir/mopack', [pkg])
            mo.assert_called_with('/path/to/builddir/mopack/apt.log', 'w')
            mc.assert_called_with(['sudo', 'apt-get', 'install', '-y', 'foo'],
                                  stdout=mo(), stderr=mo())

    def test_depends(self):
        pkg = AptPackage('foo', depends=['foo-dev', 'bar-dev'],
                         _config_file='/path/to/mopack.yml')
        self.assertEqual(pkg.depends, ['foo-dev', 'bar-dev'])

        with mock_open_log() as mo, \
             mock.patch('subprocess.check_call') as mc:  # noqa
            AptPackage.fetch_all('/path/to/builddir/mopack', [pkg])
            mo.assert_called_with('/path/to/builddir/mopack/apt.log', 'w')
            mc.assert_called_with(['sudo', 'apt-get', 'install', '-y',
                                   'foo-dev', 'bar-dev'],
                                  stdout=mo(), stderr=mo())

    def test_multiple(self):
        pkg1 = AptPackage('foo', _config_file='/path/to/mopack.yml')
        pkg2 = AptPackage('bar', depends=['bar-dev', 'baz-dev'],
                          _config_file='/path/to/mopack.yml')

        with mock_open_log() as mo, \
             mock.patch('subprocess.check_call') as mc:  # noqa
            AptPackage.fetch_all('/path/to/builddir/mopack', [pkg1, pkg2])
            mo.assert_called_with('/path/to/builddir/mopack/apt.log', 'w')
            mc.assert_called_with(['sudo', 'apt-get', 'install', '-y', 'foo',
                                   'bar-dev', 'baz-dev'],
                                  stdout=mo(), stderr=mo())
