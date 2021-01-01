from os.path import normpath
from unittest import mock, TestCase

from mopack.config import *
from mopack.options import Options
from mopack.yaml_tools import YamlParseError
from mopack.sources.apt import AptPackage
from mopack.sources.conan import ConanPackage
from mopack.sources.sdist import DirectoryPackage

foobar_cfg = 'packages:\n  foo:\n    source: apt\n\n  bar:\n    source: apt\n'
foo_cfg = 'packages:\n  foo:\n    source: apt\n    remote: libfoo1-dev\n'
bar_cfg = 'packages:\n  bar:\n    source: apt\n    remote: libbar1-dev\n'


def mock_open_files(files):
    def wrapper(filename, *args, **kwargs):
        return mock.mock_open(read_data=files[os.path.basename(filename)])(
            filename, *args, **kwargs
        )

    return wrapper


class TestConfig(TestCase):
    default_opts = Options.default()

    def test_empty_file(self):
        with mock.patch('builtins.open', mock_open_files({'mopack.yml': ''})):
            cfg = Config(['mopack.yml'])
        cfg.finalize()

        opts = Options.default()
        self.assertEqual(cfg.options, opts)
        self.assertEqual(list(cfg.packages.items()), [])

    def test_single_file(self):
        files = {'mopack.yml': foobar_cfg}
        with mock.patch('builtins.open', mock_open_files(files)):
            cfg = Config(['mopack.yml'])
        self.assertEqual(list(cfg.packages.items()), [
            ('foo', AptPackage('foo', _options=self.default_opts,
                               config_file='mopack.yml')),
            ('bar', AptPackage('bar', _options=self.default_opts,
                               config_file='mopack.yml')),
        ])

    def test_multiple_files(self):
        files = {'mopack-foo.yml': foo_cfg, 'mopack-bar.yml': bar_cfg}
        with mock.patch('builtins.open', mock_open_files(files)):
            # Filenames are in reversed order from file data, since Config
            # loads last-to-first.
            cfg = Config(['mopack-bar.yml', 'mopack-foo.yml'])
        self.assertEqual(list(cfg.packages.items()), [
            ('foo', AptPackage('foo', remote='libfoo1-dev',
                               _options=self.default_opts,
                               config_file='mopack.yml')),
            ('bar', AptPackage('bar', remote='libbar1-dev',
                               _options=self.default_opts,
                               config_file='mopack2.yml')),
        ])

    def test_directory(self):
        def exists(p):
            return os.path.basename(p) == 'dir'

        files = {'mopack.yml': foo_cfg, 'mopack-local.yml': bar_cfg,
                 'mopack-foobar.yml': foobar_cfg}
        with mock.patch('os.path.isdir', exists), \
             mock.patch('os.path.exists', return_value=True), \
             mock.patch('builtins.open', mock_open_files(files)):  # noqa
            # Filenames are in reversed order from file data, since Config
            # loads last-to-first.
            cfg = Config(['dir', 'mopack-foobar.yml'])
        self.assertEqual(list(cfg.packages.items()), [
            ('bar', AptPackage('bar', remote='libbar1-dev',
                               _options=self.default_opts,
                               config_file='mopack2.yml')),
            ('foo', AptPackage('foo', _options=self.default_opts,
                               config_file='mopack.yml')),
        ])

    def test_override(self):
        files = {'mopack-foo.yml': foo_cfg, 'mopack-foobar.yml': foobar_cfg}
        with mock.patch('builtins.open', mock_open_files(files)):
            # Filenames are in reversed order from file data, since Config
            # loads last-to-first.
            cfg = Config(['mopack-foobar.yml', 'mopack-foo.yml'])
        self.assertEqual(list(cfg.packages.items()), [
            ('foo', AptPackage('foo', remote='libfoo1-dev',
                               _options=self.default_opts,
                               config_file='mopack2.yml')),
            ('bar', AptPackage('bar', _options=self.default_opts,
                               config_file='mopack.yml')),
        ])

    def test_empty_packages(self):
        data = 'packages:'
        files = {'mopack.yml': data}
        with mock.patch('builtins.open', mock_open_files(files)):
            cfg = Config(['mopack.yml'])
        cfg.finalize()

        opts = Options.default()
        self.assertEqual(cfg.options, opts)
        self.assertEqual(list(cfg.packages.items()), [])

    def test_packages(self):
        data = 'packages:\n  foo:\n    source: apt\n'
        files = {'mopack.yml': data}
        with mock.patch('builtins.open', mock_open_files(files)):
            cfg = Config(['mopack.yml'])
        cfg.finalize()

        opts = Options.default()
        self.assertEqual(cfg.options, opts)

        pkg = AptPackage('foo', _options=opts, config_file='mopack.yml')
        self.assertEqual(list(cfg.packages.items()), [('foo', pkg)])

    def test_conditional_packages(self):
        data = ('packages:\n  foo:\n    - if: false\n      source: apt\n' +
                '    - source: conan\n      remote: foo/1.2.3\n')
        files = {'mopack.yml': data}
        with mock.patch('builtins.open', mock_open_files(files)):
            cfg = Config(['mopack.yml'])
        cfg.finalize()

        opts = Options.default()
        opts.add('sources', 'conan')
        self.assertEqual(cfg.options, opts)

        pkg = ConanPackage('foo', remote='foo/1.2.3', _options=opts,
                           config_file='mopack.yml')
        self.assertEqual(list(cfg.packages.items()), [('foo', pkg)])

    def test_invalid_conditional_packages(self):
        data = ('packages:\n  foo:\n    - source: apt\n' +
                '    - source: conan\n      remote: foo/1.2.3\n')
        files = {'mopack.yml': data}
        with self.assertRaises(YamlParseError), \
             mock.patch('builtins.open', mock_open_files(files)):  # noqa
            Config(['mopack.yml'])

    def test_empty_options(self):
        data = 'options:'
        files = {'mopack.yml': data}
        with mock.patch('builtins.open', mock_open_files(files)):
            cfg = Config(['mopack.yml'])
        cfg.finalize()

        opts = Options.default()
        self.assertEqual(cfg.options, opts)
        self.assertEqual(list(cfg.packages.items()), [])

    def test_common_options(self):
        data = ('options:\n  target_platform: linux\n' +
                '  env:\n    FOO: foo\n\n' +
                'packages:\n  foo:\n    source: apt\n')
        files = {'mopack.yml': data}
        with mock.patch('builtins.open', mock_open_files(files)):
            cfg = Config(['mopack.yml'])
        cfg.finalize()

        opts = Options()
        opts.common.target_platform = 'linux'
        opts.common.env = {'FOO': 'foo'}
        opts.common.finalize()
        self.assertEqual(cfg.options, opts)

        pkg = AptPackage('foo', _options=opts, config_file='mopack.yml')
        self.assertEqual(list(cfg.packages.items()), [('foo', pkg)])

    def test_multiple_common_options(self):
        data1 = ('options:\n  target_platform: linux\n' +
                 '  env:\n    FOO: foo\n\n' +
                 'packages:\n  foo:\n    source: apt\n')
        data2 = ('options:\n  target_platform: windows\n' +
                 '  env:\n    FOO: bad\n\n' +
                 'packages:\n  bar:\n    source: apt\n')
        files = {'mopack.yml': data1, 'mopack2.yml': data2}
        with mock.patch('builtins.open', mock_open_files(files)):
            cfg = Config(['mopack2.yml', 'mopack.yml'])
        cfg.finalize()

        opts = Options()
        opts.common.target_platform = 'linux'
        opts.common.env = {'FOO': 'foo'}
        opts.common.finalize()
        self.assertEqual(cfg.options, opts)

        pkg1 = AptPackage('foo', _options=opts, config_file='mopack.yml')
        pkg2 = AptPackage('bar', _options=opts, config_file='mopack.yml')
        self.assertEqual(list(cfg.packages.items()), [
            ('foo', pkg1), ('bar', pkg2)
        ])

    def test_builder_options(self):
        data = ('options:\n  builders:\n' +
                '    bfg9000:\n      toolchain: toolchain.bfg\n' +
                '    goat:\n      sound: baah\n\n' +
                'packages:\n  foo:\n    source: apt\n' +
                '  bar:\n    source: directory\n    path: /path/to/src\n' +
                '    build: bfg9000\n')
        files = {'mopack.yml': data}
        with mock.patch('builtins.open', mock_open_files(files)):
            cfg = Config(['mopack.yml'])
        cfg.finalize()

        opts = Options.default()
        opts.add('builders', 'bfg9000')
        opts.builders['bfg9000'].toolchain = os.path.abspath('toolchain.bfg')
        self.assertEqual(cfg.options, opts)

        pkg1 = AptPackage('foo', _options=opts, config_file='mopack.yml')
        pkg2 = DirectoryPackage('bar', path=normpath('/path/to/src'),
                                build='bfg9000', _options=opts,
                                config_file='mopack.yml')
        self.assertEqual(list(cfg.packages.items()), [
            ('foo', pkg1), ('bar', pkg2)
        ])

    def test_multiple_builder_options(self):
        data1 = ('options:\n  builders:\n' +
                 '    bfg9000:\n      toolchain: toolchain.bfg\n\n' +
                 'packages:\n  foo:\n    source: apt\n')
        data2 = ('options:\n  builders:\n' +
                 '    bfg9000:\n      toolchain: bad.bfg\n\n' +
                 'packages:\n  bar:\n    source: directory\n' +
                 '    path: /path/to/src\n    build: bfg9000\n')
        files = {'mopack.yml': data1, 'mopack2.yml': data2}
        with mock.patch('builtins.open', mock_open_files(files)):
            cfg = Config(['mopack2.yml', 'mopack.yml'])
        cfg.finalize()

        opts = Options.default()
        opts.add('builders', 'bfg9000')
        opts.builders['bfg9000'].toolchain = os.path.abspath('toolchain.bfg')
        self.assertEqual(cfg.options, opts)

        pkg1 = AptPackage('foo', _options=opts, config_file='mopack.yml')
        pkg2 = DirectoryPackage('bar', path=normpath('/path/to/src'),
                                build='bfg9000', _options=opts,
                                config_file='mopack.yml')
        self.assertEqual(list(cfg.packages.items()), [
            ('foo', pkg1), ('bar', pkg2)
        ])

    def test_source_options(self):
        data = ('options:\n  sources:\n    conan:\n      extra_args: foo\n' +
                '    goat:\n      sound: baah\n\n' +
                'packages:\n  foo:\n    source: apt\n' +
                '  bar:\n    source: conan\n    remote: bar/1.2.3\n')
        files = {'mopack.yml': data}
        with mock.patch('builtins.open', mock_open_files(files)):
            cfg = Config(['mopack.yml'])
        cfg.finalize()

        opts = Options.default()
        opts.add('sources', 'conan')
        opts.sources['conan'].extra_args.append('foo')
        self.assertEqual(cfg.options, opts)

        pkg1 = AptPackage('foo', _options=opts, config_file='mopack.yml')
        pkg2 = ConanPackage('bar', remote='bar/1.2.3', _options=opts,
                            config_file='mopack.yml')
        self.assertEqual(list(cfg.packages.items()), [
            ('foo', pkg1), ('bar', pkg2)
        ])

    def test_multiple_source_options(self):
        data1 = ('options:\n  sources:\n    conan:\n      extra_args: B\n')
        data2 = ('options:\n  sources:\n    conan:\n' +
                 '      extra_args: C\n      final: true\n\n' +
                 'packages:\n  foo:\n    source: apt\n')
        data3 = ('options:\n  sources:\n    conan:\n      extra_args: D\n\n' +
                 'packages:\n  bar:\n    source: conan\n    remote: bar/1.2.3')
        files = {'mopack.yml': data1, 'mopack2.yml': data2,
                 'mopack3.yml': data3}
        with mock.patch('builtins.open', mock_open_files(files)):
            cfg = Config(['mopack3.yml', 'mopack2.yml', 'mopack.yml'],
                         {'sources': {'conan': {'extra_args': 'A'}}})
        cfg.finalize()

        opts = Options.default()
        opts.add('sources', 'conan')
        opts.sources['conan'].extra_args.extend(['A', 'B', 'C'])
        self.assertEqual(cfg.options, opts)

        pkg1 = AptPackage('foo', _options=opts, config_file='mopack.yml')
        pkg2 = ConanPackage('bar', remote='bar/1.2.3', _options=opts,
                            config_file='mopack.yml')
        self.assertEqual(list(cfg.packages.items()), [
            ('foo', pkg1), ('bar', pkg2)
        ])


class TestChildConfig(TestCase):
    default_opts = Options.default()

    def test_empty_file(self):
        files = {'mopack.yml': '', 'mopack-child.yml': ''}
        with mock.patch('builtins.open', mock_open_files(files)):
            parent = Config(['mopack.yml'])

        with mock.patch('builtins.open', mock_open_files(files)):
            child = ChildConfig(['mopack-child.yml'], parent=parent)
        self.assertEqual(list(child.packages.items()), [])

        parent.finalize()

        opts = Options.default()
        self.assertEqual(parent.options, opts)
        self.assertEqual(list(parent.packages.items()), [])

    def test_export_config(self):
        cfg = 'export:\n  build: bfg9000\n  usage: pkg-config\n' + bar_cfg
        files = {'mopack.yml': '', 'mopack-child.yml': cfg}
        with mock.patch('builtins.open', mock_open_files(files)):
            parent = Config(['mopack.yml'])

        with mock.patch('builtins.open', mock_open_files(files)):
            child = ChildConfig(['mopack-child.yml'], parent=parent)
        self.assertEqual(child.export.build, 'bfg9000')
        self.assertEqual(child.export.usage, 'pkg-config')

    def test_child_in_parent(self):
        files = {'mopack.yml': foobar_cfg, 'mopack-child.yml': foo_cfg}
        with mock.patch('builtins.open', mock_open_files(files)):
            parent = Config(['mopack.yml'])
        with mock.patch('builtins.open', mock_open_files(files)):
            child = ChildConfig(['mopack-child.yml'], parent=parent)
        self.assertEqual(list(child.packages.items()), [
            ('foo', PlaceholderPackage)
        ])

        parent.add_children([child])
        self.assertEqual(list(parent.packages.items()), [
            ('foo', AptPackage('foo', _options=self.default_opts,
                               config_file='mopack.yml')),
            ('bar', AptPackage('bar', _options=self.default_opts,
                               config_file='mopack.yml')),
        ])

    def test_child_not_in_parent(self):
        files = {'mopack.yml': foo_cfg, 'mopack-child.yml': bar_cfg}
        with mock.patch('builtins.open', mock_open_files(files)):
            parent = Config(['mopack.yml'])
        with mock.patch('builtins.open', mock_open_files(files)):
            child = ChildConfig(['mopack-child.yml'], parent=parent)
        self.assertEqual(list(child.packages.items()), [
            ('bar', AptPackage('bar', remote='libbar1-dev',
                               _options=self.default_opts,
                               config_file='mopack-child.yml')),
        ])

        parent.add_children([child])
        self.assertEqual(list(parent.packages.items()), [
            ('bar', AptPackage('bar', remote='libbar1-dev',
                               _options=self.default_opts,
                               config_file='mopack-child.yml')),
            ('foo', AptPackage('foo', remote='libfoo1-dev',
                               _options=self.default_opts,
                               config_file='mopack.yml')),
        ])

    def test_child_mixed_in_parent(self):
        files = {'mopack.yml': foo_cfg, 'mopack-child.yml': foobar_cfg}
        with mock.patch('builtins.open', mock_open_files(files)):
            parent = Config(['mopack.yml'])
        with mock.patch('builtins.open', mock_open_files(files)):
            child = ChildConfig(['mopack-child.yml'], parent=parent)
        self.assertEqual(list(child.packages.items()), [
            ('foo', PlaceholderPackage),
            ('bar', AptPackage('bar', _options=self.default_opts,
                               config_file='mopack-child.yml')),
        ])

        parent.add_children([child])
        self.assertEqual(list(parent.packages.items()), [
            ('foo', AptPackage('foo', remote='libfoo1-dev',
                               _options=self.default_opts,
                               config_file='mopack.yml')),
            ('bar', AptPackage('bar', _options=self.default_opts,
                               config_file='mopack-child.yml')),
        ])

    def test_child_duplicate(self):
        files = {'mopack-child1.yml': foo_cfg, 'mopack-child2.yml': foo_cfg}
        parent = Config([])
        with mock.patch('builtins.open', mock_open_files(files)):
            child1 = ChildConfig(['mopack-child1.yml'], parent=parent)
        with mock.patch('builtins.open', mock_open_files(files)):
            child2 = ChildConfig(['mopack-child2.yml'], parent=parent)

        parent.add_children([child1, child2])
        self.assertEqual(list(parent.packages.items()), [
            ('foo', AptPackage('foo', remote='libfoo1-dev',
                               _options=self.default_opts,
                               config_file='mopack.yml')),
        ])

    def test_child_conflicts(self):
        files = {'mopack-child1.yml': foobar_cfg, 'mopack-child2.yml': foo_cfg}
        parent = Config([])
        with mock.patch('builtins.open', mock_open_files(files)):
            child1 = ChildConfig(['mopack-child1.yml'], parent=parent)
        with mock.patch('builtins.open', mock_open_files(files)):
            child2 = ChildConfig(['mopack-child2.yml'], parent=parent)

        with self.assertRaises(ValueError):
            parent.add_children([child1, child2])

    def test_builder_options(self):
        data = ('options:\n  builders:\n' +
                '    bfg9000:\n      toolchain: toolchain.bfg\n' +
                '    goat:\n      sound: baah\n\n' +
                'packages:\n  foo:\n    source: apt\n' +
                '  bar:\n    source: directory\n    path: /path/to/src\n' +
                '    build: bfg9000\n')
        files = {'mopack.yml': '', 'mopack-child.yml': data}

        with mock.patch('builtins.open', mock_open_files(files)):
            parent = Config(['mopack.yml'])
        with mock.patch('builtins.open', mock_open_files(files)):
            child = ChildConfig(['mopack-child.yml'], parent=parent)

        parent.add_children([child])
        parent.finalize()

        opts = Options.default()
        opts.add('builders', 'bfg9000')
        self.assertEqual(parent.options, opts)

        pkg1 = AptPackage('foo', _options=opts, config_file='mopack.yml')
        pkg2 = DirectoryPackage('bar', path=normpath('/path/to/src'),
                                build='bfg9000', _options=opts,
                                config_file='mopack.yml')
        self.assertEqual(list(parent.packages.items()), [
            ('foo', pkg1), ('bar', pkg2)
        ])

    def test_source_options(self):
        data1 = ('options:\n  sources:\n    conan:\n      extra_args: foo\n')
        data2 = ('options:\n  sources:\n    conan:\n      extra_args: bar\n' +
                 '    goat:\n      sound: baah\n\n' +
                 'packages:\n  foo:\n    source: apt\n' +
                 '  bar:\n    source: conan\n    remote: bar/1.2.3\n')
        files = {'mopack.yml': data1, 'mopack-child.yml': data2}

        with mock.patch('builtins.open', mock_open_files(files)):
            parent = Config(['mopack.yml'])
        with mock.patch('builtins.open', mock_open_files(files)):
            child = ChildConfig(['mopack-child.yml'], parent=parent)

        parent.add_children([child])
        parent.finalize()

        opts = Options.default()
        opts.add('sources', 'conan')
        opts.sources['conan'].extra_args.extend(['foo', 'bar'])
        self.assertEqual(parent.options, opts)

        pkg1 = AptPackage('foo', _options=opts, config_file='mopack.yml')
        pkg2 = ConanPackage('bar', remote='bar/1.2.3', _options=opts,
                            config_file='mopack.yml')
        self.assertEqual(list(parent.packages.items()), [
            ('foo', pkg1), ('bar', pkg2)
        ])
