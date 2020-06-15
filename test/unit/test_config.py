from os.path import abspath
from unittest import mock, TestCase

from mopack.config import *
from mopack.builders.bfg9000 import Bfg9000Builder
from mopack.sources.apt import AptPackage
from mopack.sources.conan import ConanPackage
from mopack.sources.sdist import DirectoryPackage

foobar_cfg = 'packages:\n  foo:\n    source: apt\n\n  bar:\n    source: apt\n'
foo_cfg = 'packages:\n  foo:\n    source: apt\n    remote: libfoo1-dev\n'
bar_cfg = 'packages:\n  bar:\n    source: apt\n    remote: libbar1-dev\n'


def mock_open_files(*files):
    i = iter(files)

    def wrapper(*args, **kwargs):
        return mock.mock_open(read_data=next(i))(*args, **kwargs)

    return wrapper


class TestConfig(TestCase):
    def test_empty_file(self):
        with mock.patch('builtins.open', mock_open_files('')):
            cfg = Config(['mopack.yml'])
        cfg.finalize()

        opts = {'common': CommonOptions(), 'builders': {}, 'sources': {}}
        opts['common'].finalize()
        self.assertEqual(cfg.options, opts)
        self.assertEqual(list(cfg.packages.items()), [])

    def test_single_file(self):
        with mock.patch('builtins.open', mock_open_files(foobar_cfg)):
            cfg = Config(['mopack.yml'])
        self.assertEqual(list(cfg.packages.items()), [
            ('foo', AptPackage('foo', config_file='mopack.yml')),
            ('bar', AptPackage('bar', config_file='mopack.yml')),
        ])

    def test_multiple_files(self):
        with mock.patch('builtins.open', mock_open_files(foo_cfg, bar_cfg)):
            # Filenames are in reversed order from file data, since Config
            # loads last-to-first.
            cfg = Config(['mopack-bar.yml', 'mopack-foo.yml'])
        self.assertEqual(list(cfg.packages.items()), [
            ('foo', AptPackage('foo', remote='libfoo1-dev',
                               config_file='mopack.yml')),
            ('bar', AptPackage('bar', remote='libbar1-dev',
                               config_file='mopack2.yml')),
        ])

    def test_override(self):
        with mock.patch('builtins.open', mock_open_files(foo_cfg, foobar_cfg)):
            # Filenames are in reversed order from file data, since Config
            # loads last-to-first.
            cfg = Config(['mopack-foobar.yml', 'mopack-foo.yml'])
        self.assertEqual(list(cfg.packages.items()), [
            ('foo', AptPackage('foo', remote='libfoo1-dev',
                               config_file='mopack2.yml')),
            ('bar', AptPackage('bar', config_file='mopack.yml')),
        ])

    def test_empty_packages(self):
        data = 'packages:'
        with mock.patch('builtins.open', mock_open_files(data)):
            cfg = Config(['mopack.yml'])
        cfg.finalize()

        opts = {'common': CommonOptions(), 'builders': {}, 'sources': {}}
        opts['common'].finalize()
        self.assertEqual(cfg.options, opts)
        self.assertEqual(list(cfg.packages.items()), [])

    def test_empty_options(self):
        data = 'options:'
        with mock.patch('builtins.open', mock_open_files(data)):
            cfg = Config(['mopack.yml'])
        cfg.finalize()

        opts = {'common': CommonOptions(), 'builders': {}, 'sources': {}}
        opts['common'].finalize()
        self.assertEqual(cfg.options, opts)
        self.assertEqual(list(cfg.packages.items()), [])

    def test_common_options(self):
        data = ('options:\n  target_platform: linux\n' +
                '  env:\n    FOO: foo\n\n' +
                'packages:\n  foo:\n    source: apt\n')
        with mock.patch('builtins.open', mock_open_files(data)):
            cfg = Config(['mopack.yml'])
        cfg.finalize()

        common_opts = CommonOptions()
        common_opts.target_platform = 'linux'
        common_opts.env = {'FOO': 'foo'}
        common_opts.finalize()
        opts = {'common': common_opts, 'builders': {}, 'sources': {}}
        self.assertEqual(cfg.options, opts)

        pkg = AptPackage('foo', config_file='mopack.yml')
        pkg.set_options(opts)
        self.assertEqual(list(cfg.packages.items()), [('foo', pkg)])

    def test_multiple_common_options(self):
        data1 = ('options:\n  target_platform: linux\n' +
                 '  env:\n    FOO: foo\n\n' +
                 'packages:\n  foo:\n    source: apt\n')
        data2 = ('options:\n  target_platform: windows\n' +
                 '  env:\n    FOO: bad\n\n' +
                 'packages:\n  bar:\n    source: apt\n')
        with mock.patch('builtins.open', mock_open_files(data1, data2)):
            cfg = Config(['mopack.yml', 'mopack2.yml'])
        cfg.finalize()

        common_opts = CommonOptions()
        common_opts.target_platform = 'linux'
        common_opts.env = {'FOO': 'foo'}
        common_opts.finalize()
        opts = {'common': common_opts, 'builders': {}, 'sources': {}}
        self.assertEqual(cfg.options, opts)

        pkg1 = AptPackage('foo', config_file='mopack.yml')
        pkg1.set_options(opts)
        pkg2 = AptPackage('bar', config_file='mopack.yml')
        pkg2.set_options(opts)
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
        with mock.patch('builtins.open', mock_open_files(data)):
            cfg = Config(['mopack.yml'])
        cfg.finalize()

        bfg_opts = Bfg9000Builder.Options()
        bfg_opts.toolchain = 'toolchain.bfg'
        opts = {'common': CommonOptions(), 'builders': {'bfg9000': bfg_opts},
                'sources': {}}
        opts['common'].finalize()
        self.assertEqual(cfg.options, opts)

        pkg1 = AptPackage('foo', config_file='mopack.yml')
        pkg1.set_options(opts)
        pkg2 = DirectoryPackage('bar', path=abspath('/path/to/src'),
                                build='bfg9000', config_file='mopack.yml')
        pkg2.set_options(opts)
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
        with mock.patch('builtins.open', mock_open_files(data1, data2)):
            cfg = Config(['mopack.yml', 'mopack2.yml'])
        cfg.finalize()

        bfg_opts = Bfg9000Builder.Options()
        bfg_opts.toolchain = 'toolchain.bfg'
        opts = {'common': CommonOptions(), 'builders': {'bfg9000': bfg_opts},
                'sources': {}}
        opts['common'].finalize()
        self.assertEqual(cfg.options, opts)

        pkg1 = AptPackage('foo', config_file='mopack.yml')
        pkg1.set_options(opts)
        pkg2 = DirectoryPackage('bar', path=abspath('/path/to/src'),
                                build='bfg9000', config_file='mopack.yml')
        pkg2.set_options(opts)
        self.assertEqual(list(cfg.packages.items()), [
            ('foo', pkg1), ('bar', pkg2)
        ])

    def test_source_options(self):
        data = ('options:\n  sources:\n    conan:\n      generator: cmake\n' +
                '    goat:\n      sound: baah\n\n' +
                'packages:\n  foo:\n    source: apt\n' +
                '  bar:\n    source: conan\n    remote: bar/1.2.3\n')
        with mock.patch('builtins.open', mock_open_files(data)):
            cfg = Config(['mopack.yml'])
        cfg.finalize()

        conan_opts = ConanPackage.Options()
        conan_opts.generator.append('cmake')
        opts = {'common': CommonOptions(), 'builders': {},
                'sources': {'conan': conan_opts}}
        opts['common'].finalize()
        self.assertEqual(cfg.options, opts)

        pkg1 = AptPackage('foo', config_file='mopack.yml')
        pkg1.set_options(opts)
        pkg2 = ConanPackage('bar', remote='bar/1.2.3',
                            config_file='mopack.yml')
        pkg2.set_options(opts)
        self.assertEqual(list(cfg.packages.items()), [
            ('foo', pkg1), ('bar', pkg2)
        ])

    def test_multiple_source_options(self):
        data1 = ('options:\n  sources:\n    conan:\n      generator: cmake\n')
        data2 = ('options:\n  sources:\n    conan:\n      generator: make\n' +
                 '      final: true\n\n' +
                 'packages:\n  foo:\n    source: apt\n')
        data3 = ('options:\n  sources:\n    conan:\n      generator: bad\n\n' +
                 'packages:\n  bar:\n    source: conan\n    remote: bar/1.2.3')
        with mock.patch('builtins.open', mock_open_files(data1, data2, data3)):
            cfg = Config(['mopack.yml', 'mopack2.yml', 'mopack3.yml'],
                         {'sources': {'conan': {'generator': 'txt'}}})
        cfg.finalize()

        conan_opts = ConanPackage.Options()
        conan_opts.generator.extend(['txt', 'cmake', 'make'])
        opts = {'common': CommonOptions(), 'builders': {},
                'sources': {'conan': conan_opts}}
        opts['common'].finalize()
        self.assertEqual(cfg.options, opts)

        pkg1 = AptPackage('foo', config_file='mopack.yml')
        pkg1.set_options(opts)
        pkg2 = ConanPackage('bar', remote='bar/1.2.3',
                            config_file='mopack.yml')
        pkg2.set_options(opts)
        self.assertEqual(list(cfg.packages.items()), [
            ('foo', pkg1), ('bar', pkg2)
        ])


class TestChildConfig(TestCase):
    def test_empty_file(self):
        with mock.patch('builtins.open', mock_open_files('')):
            parent = Config(['mopack.yml'])

        with mock.patch('builtins.open', mock_open_files('')):
            child = ChildConfig(['mopack-child.yml'], parent=parent)
        self.assertEqual(list(child.packages.items()), [])

        parent.finalize()

        opts = {'common': CommonOptions(), 'builders': {}, 'sources': {}}
        opts['common'].finalize()
        self.assertEqual(parent.options, opts)
        self.assertEqual(list(parent.packages.items()), [])

    def test_self_config(self):
        with mock.patch('builtins.open', mock_open_files('')):
            parent = Config(['mopack.yml'])

        cfg = 'self:\n  build: bfg9000\n  usage: pkg-config\n' + bar_cfg
        with mock.patch('builtins.open', mock_open_files(cfg)):
            child = ChildConfig(['mopack-child.yml'], parent=parent)
        self.assertEqual(child.build, 'bfg9000')
        self.assertEqual(child.usage, 'pkg-config')

    def test_child_in_parent(self):
        with mock.patch('builtins.open', mock_open_files(foobar_cfg)):
            parent = Config(['mopack.yml'])
        with mock.patch('builtins.open', mock_open_files(foo_cfg)):
            child = ChildConfig(['mopack-child.yml'], parent=parent)
        self.assertEqual(list(child.packages.items()), [
            ('foo', PlaceholderPackage)
        ])

        parent.add_children([child])
        self.assertEqual(list(parent.packages.items()), [
            ('foo', AptPackage('foo', config_file='mopack.yml')),
            ('bar', AptPackage('bar', config_file='mopack.yml')),
        ])

    def test_child_not_in_parent(self):
        with mock.patch('builtins.open', mock_open_files(foo_cfg)):
            parent = Config(['mopack.yml'])
        with mock.patch('builtins.open', mock_open_files(bar_cfg)):
            child = ChildConfig(['mopack-child.yml'], parent=parent)
        self.assertEqual(list(child.packages.items()), [
            ('bar', AptPackage('bar', remote='libbar1-dev',
                               config_file='mopack-child.yml')),
        ])

        parent.add_children([child])
        self.assertEqual(list(parent.packages.items()), [
            ('bar', AptPackage('bar', remote='libbar1-dev',
                               config_file='mopack-child.yml')),
            ('foo', AptPackage('foo', remote='libfoo1-dev',
                               config_file='mopack.yml')),
        ])

    def test_child_mixed_in_parent(self):
        with mock.patch('builtins.open', mock_open_files(foo_cfg)):
            parent = Config(['mopack.yml'])
        with mock.patch('builtins.open', mock_open_files(foobar_cfg)):
            child = ChildConfig(['mopack-child.yml'], parent=parent)
        self.assertEqual(list(child.packages.items()), [
            ('foo', PlaceholderPackage),
            ('bar', AptPackage('bar', config_file='mopack-child.yml')),
        ])

        parent.add_children([child])
        self.assertEqual(list(parent.packages.items()), [
            ('foo', AptPackage('foo', remote='libfoo1-dev',
                               config_file='mopack.yml')),
            ('bar', AptPackage('bar', config_file='mopack-child.yml')),
        ])

    def test_child_duplicate(self):
        parent = Config([])
        with mock.patch('builtins.open', mock_open_files(foo_cfg)):
            child1 = ChildConfig(['mopack-child1.yml'], parent=parent)
        with mock.patch('builtins.open', mock_open_files(foo_cfg)):
            child2 = ChildConfig(['mopack-child2.yml'], parent=parent)

        parent.add_children([child1, child2])
        self.assertEqual(list(parent.packages.items()), [
            ('foo', AptPackage('foo', remote='libfoo1-dev',
                               config_file='mopack.yml')),
        ])

    def test_child_conflicts(self):
        parent = Config([])
        with mock.patch('builtins.open', mock_open_files(foobar_cfg)):
            child1 = ChildConfig(['mopack-child1.yml'], parent=parent)
        with mock.patch('builtins.open', mock_open_files(foo_cfg)):
            child2 = ChildConfig(['mopack-child2.yml'], parent=parent)

        with self.assertRaises(ValueError):
            parent.add_children([child1, child2])

    def test_builder_options(self):
        with mock.patch('builtins.open', mock_open_files('')):
            parent = Config(['mopack.yml'])

        data = ('options:\n  builders:\n' +
                '    bfg9000:\n      toolchain: toolchain.bfg\n' +
                '    goat:\n      sound: baah\n\n' +
                'packages:\n  foo:\n    source: apt\n' +
                '  bar:\n    source: directory\n    path: /path/to/src\n' +
                '    build: bfg9000\n')
        with mock.patch('builtins.open', mock_open_files(data)):
            child = ChildConfig(['mopack-child.yml'], parent=parent)

        parent.add_children([child])
        parent.finalize()

        bfg_opts = Bfg9000Builder.Options()
        opts = {'common': CommonOptions(), 'builders': {'bfg9000': bfg_opts},
                'sources': {}}
        opts['common'].finalize()
        self.assertEqual(parent.options, opts)

        pkg1 = AptPackage('foo', config_file='mopack.yml')
        pkg1.set_options(opts)
        pkg2 = DirectoryPackage('bar', path=abspath('/path/to/src'),
                                build='bfg9000', config_file='mopack.yml')
        pkg2.set_options(opts)
        self.assertEqual(list(parent.packages.items()), [
            ('foo', pkg1), ('bar', pkg2)
        ])

    def test_source_options(self):
        data = ('options:\n  sources:\n    conan:\n      generator: make\n')
        with mock.patch('builtins.open', mock_open_files(data)):
            parent = Config(['mopack.yml'])

        data = ('options:\n  sources:\n    conan:\n      generator: cmake\n' +
                '    goat:\n      sound: baah\n\n' +
                'packages:\n  foo:\n    source: apt\n' +
                '  bar:\n    source: conan\n    remote: bar/1.2.3\n')
        with mock.patch('builtins.open', mock_open_files(data)):
            child = ChildConfig(['mopack-child.yml'], parent=parent)

        parent.add_children([child])
        parent.finalize()

        conan_opts = ConanPackage.Options()
        conan_opts.generator.extend(['make', 'cmake'])
        opts = {'common': CommonOptions(), 'builders': {},
                'sources': {'conan': conan_opts}}
        opts['common'].finalize()
        self.assertEqual(parent.options, opts)

        pkg1 = AptPackage('foo', config_file='mopack.yml')
        pkg1.set_options(opts)
        pkg2 = ConanPackage('bar', remote='bar/1.2.3',
                            config_file='mopack.yml')
        pkg2.set_options(opts)
        self.assertEqual(list(parent.packages.items()), [
            ('foo', pkg1), ('bar', pkg2)
        ])
