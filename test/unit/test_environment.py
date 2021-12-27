from unittest import mock, TestCase

from mopack.environment import *
from mopack.environment import _make_command_converter


class TestWhich(TestCase):
    def setUp(self):
        self.env = {'PATH': '/usr/bin{}/usr/local/bin'.format(os.pathsep)}

    def test_simple(self):
        with mock.patch('os.path.exists', return_value=True):
            self.assertEqual(which('python', env=self.env), ['python'])

    def test_multiword(self):
        with mock.patch('os.path.exists', return_value=True):
            self.assertEqual(which('python --foo', env=self.env),
                             ['python', '--foo'])

    def test_abs(self):
        with mock.patch('os.path.exists', return_value=True):
            self.assertEqual(which('/path/to/python', env=self.env),
                             ['/path/to/python'])

    def test_multiple(self):
        with mock.patch('os.path.exists', side_effect=[False, False, True]):
            self.assertEqual(which(['python', 'python3'], env=self.env),
                             ['python3'])

    def test_multiple_args(self):
        with mock.patch('os.path.exists', side_effect=[False, False, True]):
            self.assertEqual(which(['python', ['python3', '--foo']],
                                   env=self.env), ['python3', '--foo'])

    def test_resolve(self):
        with mock.patch('os.path.exists', side_effect=[False, True]):
            self.assertEqual(which('python', env=self.env, resolve=True),
                             [os.path.normpath('/usr/local/bin/python')])

    def test_path_ext(self):
        env = {'PATH': '/usr/bin', 'PATHEXT': '.exe'}
        with mock.patch('mopack.environment.platform_name',
                        return_value='windows'), \
             mock.patch('os.path.exists', side_effect=[False, True]):
            self.assertEqual(which('python', env=env), ['python'])

        with mock.patch('mopack.environment.platform_name',
                        return_value='windows'), \
             mock.patch('os.path.exists', side_effect=[False, True]):
            self.assertEqual(which('python', env=env, resolve=True),
                             [os.path.normpath('/usr/bin/python.exe')])

        with mock.patch('mopack.environment.platform_name',
                        return_value='windows'), \
             mock.patch('os.path.exists', side_effect=[False, True]):
            self.assertEqual(
                which([['python', '--foo']], env=env, resolve=True),
                [os.path.normpath('/usr/bin/python.exe'), '--foo']
            )

    def test_not_found(self):
        with mock.patch('os.path.exists', return_value=False):
            self.assertRaises(IOError, which, 'python', env=self.env)
        self.assertRaises(IOError, which, 'python', env={'PATH': ''})

    def test_empty(self):
        self.assertRaises(TypeError, which, [])


class TestMakeCommandConverter(TestCase):
    def test_simple(self):
        converter = _make_command_converter([('gcc', 'g++')])
        self.assertEqual(converter('gcc'), 'g++')
        self.assertEqual(converter('foo-gcc'), 'foo-g++')
        self.assertEqual(converter('gcc-foo'), 'g++-foo')

        self.assertEqual(converter('foo'), None)
        self.assertEqual(converter('foogcc'), None)
        self.assertEqual(converter('gccfoo'), None)

    def test_order(self):
        converter = _make_command_converter([
            ('clang-cl', 'clang-cl++'),
            ('clang', 'clang++'),
        ])

        self.assertEqual(converter('clang'), 'clang++')
        self.assertEqual(converter('foo-clang'), 'foo-clang++')
        self.assertEqual(converter('clang-foo'), 'clang++-foo')

        self.assertEqual(converter('clang-cl'), 'clang-cl++')
        self.assertEqual(converter('foo-clang-cl'), 'foo-clang-cl++')
        self.assertEqual(converter('clang-cl-foo'), 'clang-cl++-foo')

        self.assertEqual(converter('foo'), None)

    def test_regex(self):
        converter = _make_command_converter([
            (re.compile(r'gcc(?:-[\d.]+)?(?:-(?:posix|win32))?'), 'windres'),
        ])

        self.assertEqual(converter('gcc'), 'windres')
        self.assertEqual(converter('gcc-9.1'), 'windres')
        self.assertEqual(converter('gcc-posix'), 'windres')
        self.assertEqual(converter('gcc-win32'), 'windres')
        self.assertEqual(converter('gcc-9.1-posix'), 'windres')
        self.assertEqual(converter('gcc-9.1-win32'), 'windres')
        self.assertEqual(converter('i686-w64-mingw32-gcc-9.1-win32'),
                         'i686-w64-mingw32-windres')

    def test_invalid_regex(self):
        with self.assertRaises(re.error):
            _make_command_converter([(re.compile(r'([\d.]+)'), '')])


class TestGetCCompiler(TestCase):
    def test_default(self):
        with mock.patch('os.path.exists', return_value=False):
            self.assertEqual(get_c_compiler({}), None)

    def test_explicit(self):
        with mock.patch('os.path.exists', return_value=False):
            self.assertEqual(get_c_compiler({'CC': 'gcc'}), ['gcc'])
            self.assertEqual(get_c_compiler({'CC': 'gcc --foo'}),
                             ['gcc', '--foo'])

    def test_guess_objc(self):
        with mock.patch('os.path.exists', return_value=True):
            self.assertEqual(get_c_compiler({'OBJC': 'foo-gcc'}),
                             ['foo-gcc'])

    def test_guess_cxx(self):
        with mock.patch('os.path.exists', return_value=True):
            self.assertEqual(get_c_compiler({'CXX': 'foo-g++'}),
                             ['foo-gcc'])
        with mock.patch('os.path.exists', return_value=True):
            self.assertEqual(get_c_compiler({'CXX': 'foo'}), None)

    def test_guess_objcxx(self):
        with mock.patch('os.path.exists', return_value=True):
            self.assertEqual(get_c_compiler({'OBJCXX': 'foo-g++'}),
                             ['foo-gcc'])
        with mock.patch('os.path.exists', return_value=True):
            self.assertEqual(get_c_compiler({'OBJCXX': 'foo'}), None)

    def test_guess_not_found(self):
        with mock.patch('os.path.exists', return_value=False):
            self.assertEqual(get_c_compiler({'CXX': 'foo-g++'}), None)


class TestGetPkgConfig(TestCase):
    def test_default(self):
        with mock.patch('os.path.exists', return_value=False):
            self.assertEqual(get_pkg_config({}), ['pkg-config'])

    def test_explicit(self):
        with mock.patch('os.path.exists', return_value=False):
            self.assertEqual(get_pkg_config({'PKG_CONFIG': 'pkgconf'}),
                             ['pkgconf'])
            self.assertEqual(get_pkg_config({'PKG_CONFIG': 'pkgconf --foo'}),
                             ['pkgconf', '--foo'])

    def test_guess_gcc(self):
        with mock.patch('os.path.exists', return_value=True):
            self.assertEqual(get_pkg_config({'CC': 'foo-gcc'}),
                             ['foo-pkg-config'])

    def test_guess_gxx(self):
        with mock.patch('os.path.exists', return_value=True):
            self.assertEqual(get_pkg_config({'CXX': 'foo-g++'}),
                             ['foo-pkg-config'])

    def test_guess_clang(self):
        with mock.patch('os.path.exists', return_value=True):
            self.assertEqual(get_pkg_config({'CC': 'foo-cc'}),
                             ['pkg-config'])

    def test_guess_not_found(self):
        with mock.patch('os.path.exists', return_value=False):
            self.assertEqual(get_pkg_config({'CC': 'foo-gcc'}),
                             ['pkg-config'])
