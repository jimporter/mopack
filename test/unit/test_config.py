from os.path import normpath
from textwrap import dedent
from unittest import mock, TestCase

from . import mock_open_files

from mopack.config import *
from mopack.options import Options
from mopack.yaml_tools import YamlParseError
from mopack.sources.apt import AptPackage
from mopack.sources.conan import ConanPackage
from mopack.sources.sdist import DirectoryPackage

foobar_cfg = dedent("""
  packages:
    foo: {source: apt}
    bar: {source: apt}
""")

foo_cfg = dedent("""
  packages:
    foo:
      source: apt
      remote: libfoo1-dev
""")

bar_cfg = dedent("""
  packages:
    bar:
      source: apt
      remote: libbar1-dev
""")


class MockPackage:
    def __init__(self, name):
        self.name = name


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
        data = dedent("""
          packages:
            foo:
              source: apt
        """)
        files = {'mopack.yml': data}
        with mock.patch('builtins.open', mock_open_files(files)):
            cfg = Config(['mopack.yml'])
        cfg.finalize()

        opts = Options.default()
        self.assertEqual(cfg.options, opts)

        pkg = AptPackage('foo', _options=opts, config_file='mopack.yml')
        self.assertEqual(list(cfg.packages.items()), [('foo', pkg)])

    def test_conditional_packages(self):
        data = dedent("""
          packages:
            foo:
              - if: false
                source: apt
              - source: conan
                remote: foo/1.2.3
        """)
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
        data = dedent("""
          packages:
            foo:
              - source: apt
              - source: conan
                remote: foo/1.2.3
        """)
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
        data = dedent("""
          options:
            target_platform: linux
            env:
              FOO: foo
          packages:
            foo:
              source: apt
        """)
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
        data1 = dedent("""
          options:
            target_platform: linux
            env:
              FOO: foo
          packages:
            foo:
              source: apt
        """)
        data2 = dedent("""
          options:
            target_platform: windows
            env:
              FOO: bad
          packages:
            bar:
              source: apt
        """)

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
        data = dedent("""
          options:
            builders:
              bfg9000:
                toolchain: toolchain.bfg
              goat:
                sound: baah
          packages:
            foo:
              source: apt
            bar:
              source: directory
              path: /path/to/src
              build: bfg9000
        """)
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
        data1 = dedent("""
          options:
            builders:
              bfg9000:
                toolchain: toolchain.bfg
          packages:
            foo:
              source: apt
        """)
        data2 = dedent("""
          options:
            builders:
              bfg9000:
                toolchain: bad.bfg
          packages:
            bar:
              source: directory
              path: /path/to/src
              build: bfg9000
        """)

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
        data = dedent("""
          options:
            sources:
              conan:
                extra_args: foo
              goat:
                sound: baah
          packages:
            foo:
              source: apt
            bar:
              source: conan
              remote: bar/1.2.3
        """)
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
        data1 = dedent("""
          options:
            sources:
              conan:
                extra_args: -B
        """)
        data2 = dedent("""
          options:
            sources:
              conan:
                extra_args: -C
                final: true
          packages:
            foo:
              source: apt
        """)
        data3 = dedent("""
          options:
            sources:
              conan:
                extra_args: -D
          packages:
            bar:
              source: conan
              remote: bar/1.2.3
        """)

        files = {'mopack.yml': data1, 'mopack2.yml': data2,
                 'mopack3.yml': data3}
        with mock.patch('builtins.open', mock_open_files(files)):
            cfg = Config(['mopack3.yml', 'mopack2.yml', 'mopack.yml'],
                         {'sources': {'conan': {'extra_args': '-A'}}})
        cfg.finalize()

        opts = Options.default()
        opts.add('sources', 'conan')
        opts.sources['conan'].extra_args.extend(['-A', '-B', '-C'])
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
            child = ChildConfig(['mopack-child.yml'], parent,
                                MockPackage('foo'))
        self.assertEqual(list(child.packages.items()), [])

        parent.finalize()

        opts = Options.default()
        self.assertEqual(parent.options, opts)
        self.assertEqual(list(parent.packages.items()), [])

    def test_export_config(self):
        cfg = dedent("""
        export:
          build: bfg9000
          usage: pkg_config
        """) + bar_cfg
        files = {'mopack.yml': '', 'mopack-child.yml': cfg}
        with mock.patch('builtins.open', mock_open_files(files)):
            parent = Config(['mopack.yml'])

        with mock.patch('builtins.open', mock_open_files(files)):
            child = ChildConfig(['mopack-child.yml'], parent,
                                MockPackage('foo'))
        self.assertEqual(child.export.build, 'bfg9000')
        self.assertEqual(child.export.usage, 'pkg_config')

    def test_child_in_parent(self):
        files = {'mopack.yml': foobar_cfg, 'mopack-child.yml': foo_cfg}
        with mock.patch('builtins.open', mock_open_files(files)):
            parent = Config(['mopack.yml'])
        with mock.patch('builtins.open', mock_open_files(files)):
            child = ChildConfig(['mopack-child.yml'], parent,
                                MockPackage('foo'))
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
            child = ChildConfig(['mopack-child.yml'], parent,
                                MockPackage('foo'))
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
            child = ChildConfig(['mopack-child.yml'], parent,
                                MockPackage('foo'))
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
            child1 = ChildConfig(['mopack-child1.yml'], parent,
                                 MockPackage('foo'))
        with mock.patch('builtins.open', mock_open_files(files)):
            child2 = ChildConfig(['mopack-child2.yml'], parent,
                                 MockPackage('foo'))

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
            child1 = ChildConfig(['mopack-child1.yml'], parent,
                                 MockPackage('foo'))
        with mock.patch('builtins.open', mock_open_files(files)):
            child2 = ChildConfig(['mopack-child2.yml'], parent,
                                 MockPackage('foo'))

        with self.assertRaises(ValueError):
            parent.add_children([child1, child2])

    def test_builder_options(self):
        data = dedent("""
          options:
            builders:
              bfg9000:
                toolchain: toolchain.bfg
              goat:
                sound: baah
          packages:
            foo:
              source: apt
            bar:
              source: directory
              path: /path/to/src
              build: bfg9000
        """)
        files = {'mopack.yml': '', 'mopack-child.yml': data}

        with mock.patch('builtins.open', mock_open_files(files)):
            parent = Config(['mopack.yml'])
        with mock.patch('builtins.open', mock_open_files(files)):
            child = ChildConfig(['mopack-child.yml'], parent,
                                MockPackage('foo'))

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
        data1 = dedent("""
          options:
            sources:
              conan:
                extra_args: foo
        """)
        data2 = dedent("""
          options:
            sources:
              conan:
                extra_args: bar
              goat:
                sound: baah
          packages:
            foo:
              source: apt
            bar:
              source: conan
              remote: bar/1.2.3
        """)

        files = {'mopack.yml': data1, 'mopack-child.yml': data2}

        with mock.patch('builtins.open', mock_open_files(files)):
            parent = Config(['mopack.yml'])
        with mock.patch('builtins.open', mock_open_files(files)):
            child = ChildConfig(['mopack-child.yml'], parent,
                                MockPackage('foo'))

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
