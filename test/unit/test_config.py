from unittest import mock, TestCase

from mopack.config import *
from mopack.sources.apt import AptPackage

foobar_cfg = 'packages:\n  foo:\n    source: apt\n\n  bar:\n    source: apt\n'
foo_cfg = 'packages:\n  foo:\n    source: apt\n    remote: libfoo1-dev\n'
bar_cfg = 'packages:\n  bar:\n    source: apt\n    remote: libbar1-dev\n'


def mock_open_files(*files):
    i = iter(files)

    def wrapper(*args, **kwargs):
        return mock.mock_open(read_data=next(i))(*args, **kwargs)

    return wrapper


class TestConfig(TestCase):
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

    def test_child_in_parent(self):
        with mock.patch('builtins.open', mock_open_files(foobar_cfg)):
            parent = Config(['mopack.yml'])
        with mock.patch('builtins.open', mock_open_files(foo_cfg)):
            child = Config(['mopack-child.yml'], parent=parent)
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
            child = Config(['mopack-child.yml'], parent=parent)
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
            child = Config(['mopack-child.yml'], parent=parent)
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
            child1 = Config(['mopack-child1.yml'], parent=parent)
        with mock.patch('builtins.open', mock_open_files(foo_cfg)):
            child2 = Config(['mopack-child2.yml'], parent=parent)

        parent.add_children([child1, child2])
        self.assertEqual(list(parent.packages.items()), [
            ('foo', AptPackage('foo', remote='libfoo1-dev',
                               config_file='mopack.yml')),
        ])

    def test_child_conflicts(self):
        parent = Config([])
        with mock.patch('builtins.open', mock_open_files(foobar_cfg)):
            child1 = Config(['mopack-child1.yml'], parent=parent)
        with mock.patch('builtins.open', mock_open_files(foo_cfg)):
            child2 = Config(['mopack-child2.yml'], parent=parent)

        with self.assertRaises(ValueError):
            parent.add_children([child1, child2])
