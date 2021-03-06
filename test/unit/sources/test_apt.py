import os
import subprocess
from unittest import mock

from . import SourceTest, through_json
from .. import mock_open_log

from mopack.iterutils import iterate
from mopack.sources import Package
from mopack.sources.apt import AptPackage
from mopack.sources.conan import ConanPackage


class TestApt(SourceTest):
    pkg_type = AptPackage
    config_file = '/path/to/mopack.yml'
    pkgdir = '/path/to/builddir/mopack'

    def check_resolve_all(self, packages, remotes, *, submodules=None,
                          usages=None):
        with mock_open_log() as mopen, \
             mock.patch('subprocess.run') as mcall:  # noqa
            AptPackage.resolve_all(self.pkgdir, packages)

            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'apt.log'
            ), 'a')
            for i in packages:
                if i.repository:
                    mcall.assert_any_call(
                        ['sudo', 'add-apt-repository', '-y', i.repository],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        universal_newlines=True, check=True
                    )
            mcall.assert_any_call(
                ['sudo', 'apt-get', 'update'], stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, universal_newlines=True, check=True
            )
            mcall.assert_any_call(
                ['sudo', 'apt-get', 'install', '-y'] + remotes,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, check=True
            )

        if usages is None:
            usages = []
            for pkg in packages:
                libs = ([] if pkg.submodules and pkg.submodules['required']
                        else [pkg.name])
                libs.extend('{}_{}'.format(pkg.name, i)
                            for i in iterate(submodules))
                usages.append({
                    'type': 'path', 'auto_link': False, 'include_path': [],
                    'library_path': [], 'headers': [], 'libraries': libs,
                    'compile_flags': [], 'link_flags': [],
                })

        for pkg, usage in zip(packages, usages):
            with mock.patch('subprocess.run', side_effect=OSError()):
                self.assertEqual(pkg.get_usage(self.pkgdir, submodules), usage)

    def test_basic(self):
        pkg = self.make_package('foo')
        self.assertEqual(pkg.remote, 'libfoo-dev')
        self.assertEqual(pkg.repository, None)
        self.assertEqual(pkg.needs_dependencies, False)
        self.assertEqual(pkg.should_deploy, True)
        self.check_resolve_all([pkg], ['libfoo-dev'])

    def test_remote(self):
        pkg = self.make_package('foo', remote='foo-dev')
        self.assertEqual(pkg.remote, 'foo-dev')
        self.assertEqual(pkg.repository, None)
        self.check_resolve_all([pkg], ['foo-dev'])

    def test_repository(self):
        pkg = self.make_package('foo', remote='foo-dev',
                                repository='ppa:foo/stable')
        self.assertEqual(pkg.remote, 'foo-dev')
        self.assertEqual(pkg.repository, 'ppa:foo/stable')
        self.check_resolve_all([pkg], ['foo-dev'])

    def test_multiple(self):
        pkg1 = self.make_package('foo')
        pkg2 = self.make_package('bar', remote='bar-dev')
        self.check_resolve_all([pkg1, pkg2], ['libfoo-dev', 'bar-dev'])

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        pkg = self.make_package('foo', submodules=submodules_required)
        self.check_resolve_all([pkg], ['libfoo-dev'], submodules=['sub'])

        pkg = self.make_package(
            'foo', usage={'type': 'system', 'libraries': 'bar'},
            submodules=submodules_required
        )
        self.check_resolve_all(
            [pkg], ['libfoo-dev'], submodules=['sub'], usages=[{
                'type': 'path', 'auto_link': False, 'include_path': [],
                'library_path': [], 'headers': [],
                'libraries': ['bar', 'foo_sub'], 'compile_flags': [],
                'link_flags': [],
            }]
        )

        pkg = self.make_package('foo', submodules=submodules_optional)
        self.check_resolve_all([pkg], ['libfoo-dev'], submodules=['sub'])

        pkg = self.make_package(
            'foo', usage={'type': 'system', 'libraries': 'bar'},
            submodules=submodules_optional
        )
        self.check_resolve_all(
            [pkg], ['libfoo-dev'], submodules=['sub'], usages=[{
                'type': 'path', 'auto_link': False, 'include_path': [],
                'library_path': [], 'headers': [],
                'libraries': ['bar', 'foo_sub'], 'compile_flags': [],
                'link_flags': [],
            }]
        )

    def test_invalid_submodule(self):
        pkg = self.make_package('foo', submodules={
            'names': ['sub'], 'required': True
        })
        with self.assertRaises(ValueError):
            pkg.get_usage(self.pkgdir, ['invalid'])

    def test_deploy(self):
        pkg = self.make_package('foo')
        # This is a no-op; just make sure it executes ok.
        AptPackage.deploy_all(self.pkgdir, [pkg])

    def test_clean_pre(self):
        oldpkg = self.make_package('foo')
        newpkg = self.make_package(ConanPackage, 'foo',
                                   remote='foo/1.2.4@conan/stable')

        # Apt -> Conan
        self.assertEqual(oldpkg.clean_pre(self.pkgdir, newpkg), False)

        # Apt -> nothing
        self.assertEqual(oldpkg.clean_pre(self.pkgdir, None), False)

    def test_clean_post(self):
        oldpkg = self.make_package('foo')
        newpkg = self.make_package(ConanPackage, 'foo',
                                   remote='foo/1.2.4@conan/stable')

        # Apt -> Conan
        self.assertEqual(oldpkg.clean_post(self.pkgdir, newpkg), False)

        # Apt -> nothing
        self.assertEqual(oldpkg.clean_post(self.pkgdir, None), False)

    def test_clean_all(self):
        oldpkg = self.make_package('foo')
        newpkg = self.make_package(ConanPackage, 'foo',
                                   remote='foo/1.2.4@conan/stable')

        # Apt -> Conan
        self.assertEqual(oldpkg.clean_all(self.pkgdir, newpkg), (False, False))

        # Apt -> nothing
        self.assertEqual(oldpkg.clean_all(self.pkgdir, None), (False, False))

    def test_equality(self):
        pkg = self.make_package('foo')

        self.assertEqual(pkg, self.make_package('foo'))
        self.assertEqual(pkg, self.make_package('foo', remote='libfoo-dev'))
        self.assertEqual(pkg, self.make_package(
            'foo', config_file='/path/to/mopack2.yml'
        ))

        self.assertNotEqual(pkg, self.make_package('bar'))
        self.assertNotEqual(pkg, self.make_package('bar', remote='libfoo-dev'))
        self.assertNotEqual(pkg, self.make_package('foo', remote='libbar-dev'))

    def test_rehydrate(self):
        opts = self.make_options()
        pkg = AptPackage('foo', remote='libbar-dev', _options=opts,
                         config_file=self.config_file)
        data = through_json(pkg.dehydrate())
        self.assertEqual(pkg, Package.rehydrate(data, _options=opts))
