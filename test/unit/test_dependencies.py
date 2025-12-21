from unittest import TestCase

from mopack.dependencies import Dependency


class TestDependency(TestCase):
    def test_package_string(self):
        dep = Dependency('package')
        self.assertEqual(dep.package, 'package')
        self.assertEqual(dep.submodules, None)

        dep = Dependency('red-panda')
        self.assertEqual(dep.package, 'red-panda')
        self.assertEqual(dep.submodules, None)

    def test_submodule_string(self):
        dep = Dependency('pkg[sub]')
        self.assertEqual(dep.package, 'pkg')
        self.assertEqual(dep.submodules, ['sub'])

        dep = Dependency('pkg[foo,bar]')
        self.assertEqual(dep.package, 'pkg')
        self.assertEqual(dep.submodules, ['foo', 'bar'])

    def test_invalid(self):
        not_deps = ['pkg,', 'pkg[', 'pkg]', 'pkg[]', 'pkg[sub,]', 'pkg[,sub]']
        for i in not_deps:
            with self.assertRaises(ValueError):
                Dependency(i)

    def test_dependency_components(self):
        dep = Dependency('pkg', None)
        self.assertEqual(dep.package, 'pkg')
        self.assertEqual(dep.submodules, None)

        dep = Dependency('pkg', [])
        self.assertEqual(dep.package, 'pkg')
        self.assertEqual(dep.submodules, None)

        dep = Dependency('pkg', 'foo')
        self.assertEqual(dep.package, 'pkg')
        self.assertEqual(dep.submodules, ['foo'])

        dep = Dependency('pkg', ['foo'])
        self.assertEqual(dep.package, 'pkg')
        self.assertEqual(dep.submodules, ['foo'])

        dep = Dependency('pkg', ['foo', 'bar'])
        self.assertEqual(dep.package, 'pkg')
        self.assertEqual(dep.submodules, ['foo', 'bar'])

        dep = Dependency('pkg', iter(['foo', 'bar']))
        self.assertEqual(dep.package, 'pkg')
        self.assertEqual(dep.submodules, ['foo', 'bar'])

    def test_invalid_dependency_string(self):
        not_deps = [('pkg,', None),
                    ('pkg[', None),
                    ('pkg]', None),
                    ('pkg', ['foo,']),
                    ('pkg', ['foo[']),
                    ('pkg', ['foo]']),
                    ('pkg', ['foo', 'bar['])]
        for i in not_deps:
            with self.assertRaises(ValueError):
                Dependency(*i)
