from io import StringIO
from textwrap import dedent
from unittest import mock, TestCase

from .. import mock_open_log

from mopack.sources.conan import ConanPackage


def mock_open_write():
    class MockFile(StringIO):
        def close(self):
            pass

    mock_open = mock.mock_open()

    def non_mock(*args, **kwargs):
        mock_open.side_effect = None
        mock_open.mock_file = MockFile()
        return mock_open.mock_file

    mock_open.side_effect = non_mock
    return mock_open


class TestConan(TestCase):
    def test_basic(self):
        pkg = ConanPackage('foo', remote='foo/1.2.3@conan/stable',
                           _config_file='/path/to/mopack.yml')
        self.assertEqual(pkg.remote, 'foo/1.2.3@conan/stable')
        self.assertEqual(pkg.options, {})

        with mock_open_log(mock_open_write()) as mo, \
             mock.patch('subprocess.check_call') as mc:  # noqa
            ConanPackage.fetch_all('/path/to/builddir/mopack', [pkg])
            self.assertEqual(mo.mock_file.getvalue(), dedent("""\
                [requires]
                foo/1.2.3@conan/stable

                [options]
            """))
            mc.assert_called_with([
                'conan', 'install', '-g', 'pkg_config', '-if',
                '/path/to/builddir/mopack/conan', '/path/to/builddir/mopack'
            ], stdout=mo(), stderr=mo())

    def test_options(self):
        pkg = ConanPackage('foo', remote='foo/1.2.3@conan/stable',
                           options={'shared': True},
                           _config_file='/path/to/mopack.yml')
        self.assertEqual(pkg.remote, 'foo/1.2.3@conan/stable')
        self.assertEqual(pkg.options, {'shared': True})

        with mock_open_log(mock_open_write()) as mo, \
             mock.patch('subprocess.check_call') as mc:  # noqa
            ConanPackage.fetch_all('/path/to/builddir/mopack', [pkg])
            self.assertEqual(mo.mock_file.getvalue(), dedent("""\
                [requires]
                foo/1.2.3@conan/stable

                [options]
                foo:shared=True
            """))
            mc.assert_called_with([
                'conan', 'install', '-g', 'pkg_config', '-if',
                '/path/to/builddir/mopack/conan', '/path/to/builddir/mopack'
            ], stdout=mo(), stderr=mo())

    def test_multiple(self):
        pkg1 = ConanPackage('foo', remote='foo/1.2.3@conan/stable',
                            _config_file='/path/to/mopack.yml')
        pkg2 = ConanPackage('bar', remote='bar/2.3.4@conan/stable',
                            options={'shared': True},
                            _config_file='/path/to/mopack.yml')

        with mock_open_log(mock_open_write()) as mo, \
             mock.patch('subprocess.check_call') as mc:  # noqa
            ConanPackage.fetch_all('/path/to/builddir/mopack', [pkg1, pkg2])
            self.assertEqual(mo.mock_file.getvalue(), dedent("""\
                [requires]
                foo/1.2.3@conan/stable
                bar/2.3.4@conan/stable

                [options]
                bar:shared=True
            """))
            mc.assert_called_with([
                'conan', 'install', '-g', 'pkg_config', '-if',
                '/path/to/builddir/mopack/conan', '/path/to/builddir/mopack'
            ], stdout=mo(), stderr=mo())
