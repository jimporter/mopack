import os
import subprocess
from unittest import mock

from . import OriginTest, through_json
from .. import assert_logging, mock_open_log

from mopack.iterutils import iterate
from mopack.origins import Package
from mopack.origins.apt import AptPackage
from mopack.origins.conan import ConanPackage
from mopack.types import dependency_string


def mock_run(args, **kwargs):
    if args[0] == 'dpkg-query':
        return subprocess.CompletedProcess(args, 0, '1.2.3')
    raise OSError()


class TestApt(OriginTest):
    pkg_type = AptPackage
    pkgconfdir = os.path.join(OriginTest.pkgdir, 'pkgconfig')

    def check_resolve_all(self, pkgs, remotes):
        with mock_open_log() as mopen, \
             mock.patch('subprocess.run') as mrun:
            with assert_logging([('resolve', '{} from apt'.format(i.name))
                                 for i in pkgs]):
                AptPackage.resolve_all(self.metadata, pkgs)

            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'apt.log'
            ), 'a')

            for i in pkgs:
                if i.repository:
                    mrun.assert_any_call(
                        ['sudo', 'add-apt-repository', '-y', i.repository],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        universal_newlines=True, check=True, env={}
                    )
            mrun.assert_any_call(
                ['sudo', 'apt-get', 'update'], stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, universal_newlines=True, check=True,
                env={}
            )
            mrun.assert_any_call(
                ['sudo', 'apt-get', 'install', '-y'] + remotes,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, check=True, env={}
            )

    def check_linkage(self, pkg, *, submodules=None, linkage=None):
        if linkage is None:
            depname = dependency_string(pkg.name, submodules)
            libs = ([] if pkg.submodules and pkg.submodules['required']
                    else [pkg.name])
            libs.extend('{}_{}'.format(pkg.name, i)
                        for i in iterate(submodules))

            linkage = {'name': depname, 'type': 'system', 'generated': True,
                       'auto_link': False, 'pcnames': [depname],
                       'pkg_config_path': [self.pkgconfdir]}

        with mock.patch('subprocess.run', mock_run), \
             mock.patch('mopack.linkages.path_system.PathLinkage._filter_path',
                        lambda *args: []), \
             mock.patch('mopack.linkages.path_system.file_outdated',
                        return_value=True), \
             mock.patch('os.makedirs'), \
             mock.patch('builtins.open'):
            self.assertEqual(pkg.get_linkage(self.metadata, submodules),
                             linkage)

    def test_basic(self):
        pkg = self.make_package('foo')
        self.assertEqual(pkg.remote, ['libfoo-dev'])
        self.assertEqual(pkg.repository, None)
        self.assertEqual(pkg.needs_dependencies, False)
        self.assertEqual(pkg.should_deploy, True)
        self.check_resolve_all([pkg], ['libfoo-dev'])

        with mock.patch('subprocess.run', side_effect=mock_run) as mrun:
            self.assertEqual(pkg.version(self.metadata), '1.2.3')
            mrun.assert_has_calls([
                mock.call(
                    ['pkg-config', 'foo', '--modversion'], check=True,
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                    universal_newlines=True, env={}
                ),
                mock.call(
                    ['dpkg-query', '-W', '-f${Version}', 'libfoo-dev'],
                    check=True, stdout=subprocess.PIPE,
                    universal_newlines=True, env={}
                ),
            ])

        self.check_linkage(pkg)

    def test_remote(self):
        pkg = self.make_package('foo', remote='foo-dev')
        self.assertEqual(pkg.remote, ['foo-dev'])
        self.assertEqual(pkg.repository, None)
        self.check_resolve_all([pkg], ['foo-dev'])

        with mock.patch('subprocess.run', side_effect=mock_run) as mrun:
            self.assertEqual(pkg.version(self.metadata), '1.2.3')
            mrun.assert_has_calls([
                mock.call(
                    ['pkg-config', 'foo', '--modversion'], check=True,
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                    universal_newlines=True, env={}
                ),
                mock.call(
                    ['dpkg-query', '-W', '-f${Version}', 'foo-dev'],
                    check=True, stdout=subprocess.PIPE,
                    universal_newlines=True, env={}
                ),
            ])

        self.check_linkage(pkg)

        pkg = self.make_package('foo', remote=['foo-dev', 'bar-dev'])
        self.assertEqual(pkg.remote, ['foo-dev', 'bar-dev'])
        self.assertEqual(pkg.repository, None)
        self.check_resolve_all([pkg], ['foo-dev', 'bar-dev'])

        with mock.patch('subprocess.run', side_effect=mock_run) as mrun:
            pkg.version(self.metadata)
            mrun.assert_has_calls([
                mock.call(
                    ['pkg-config', 'foo', '--modversion'], check=True,
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                    universal_newlines=True, env={}
                ),
                mock.call(
                    ['dpkg-query', '-W', '-f${Version}', 'foo-dev'],
                    check=True, stdout=subprocess.PIPE,
                    universal_newlines=True, env={}
                ),
            ])

        self.check_linkage(pkg)

    def test_repository(self):
        pkg = self.make_package('foo', remote='foo-dev',
                                repository='ppa:foo/stable')
        self.assertEqual(pkg.remote, ['foo-dev'])
        self.assertEqual(pkg.repository, 'ppa:foo/stable')
        self.check_resolve_all([pkg], ['foo-dev'])
        self.check_linkage(pkg)

    def test_explicit_version(self):
        pkg = self.make_package('foo', linkage={
            'type': 'system', 'version': '2.0',
        })
        self.assertEqual(pkg.remote, ['libfoo-dev'])
        self.assertEqual(pkg.repository, None)
        self.assertEqual(pkg.needs_dependencies, False)
        self.assertEqual(pkg.should_deploy, True)
        self.check_resolve_all([pkg], ['libfoo-dev'])

        with mock.patch('subprocess.run', side_effect=mock_run) as mrun:
            self.assertEqual(pkg.version(self.metadata), '2.0')
            mrun.assert_called_once_with(
                ['pkg-config', 'foo', '--modversion'], check=True,
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                universal_newlines=True, env={}
            )

        self.check_linkage(pkg)

    def test_multiple(self):
        pkgs = [self.make_package('foo'),
                self.make_package('bar', remote='bar-dev')]
        self.check_resolve_all(pkgs, ['libfoo-dev', 'bar-dev'])
        for pkg in pkgs:
            self.check_linkage(pkg)

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        pkg = self.make_package('foo', submodules=submodules_required)
        self.check_resolve_all([pkg], ['libfoo-dev'])
        self.check_linkage(pkg, submodules=['sub'])

        pkg = self.make_package(
            'foo', linkage={'type': 'system', 'libraries': 'bar'},
            submodules=submodules_required
        )
        self.check_resolve_all([pkg], ['libfoo-dev'])
        self.check_linkage(pkg, submodules=['sub'], linkage={
            'name': 'foo[sub]', 'type': 'system', 'generated': True,
            'auto_link': False, 'pcnames': ['foo[sub]'],
            'pkg_config_path': [self.pkgconfdir],
        })

        pkg = self.make_package('foo', submodules=submodules_optional)
        self.check_resolve_all([pkg], ['libfoo-dev'])
        self.check_linkage(pkg, submodules=['sub'])

        pkg = self.make_package(
            'foo', linkage={'type': 'system', 'libraries': 'bar'},
            submodules=submodules_optional
        )
        self.check_resolve_all([pkg], ['libfoo-dev'])
        self.check_linkage(pkg, submodules=['sub'], linkage={
            'name': 'foo[sub]', 'type': 'system', 'generated': True,
            'auto_link': False, 'pcnames': ['foo[sub]'],
            'pkg_config_path': [self.pkgconfdir],
        })

    def test_invalid_submodule(self):
        pkg = self.make_package('foo', submodules={
            'names': ['sub'], 'required': True
        })
        with self.assertRaises(ValueError):
            pkg.get_linkage(self.metadata, ['invalid'])

    def test_deploy(self):
        pkg = self.make_package('foo')
        # This is a no-op; just make sure it executes ok.
        AptPackage.deploy_all(self.metadata, [pkg])

    def test_clean_pre(self):
        oldpkg = self.make_package('foo')
        newpkg = self.make_package(ConanPackage, 'foo',
                                   remote='foo/1.2.4@conan/stable')

        # Apt -> Conan
        self.assertEqual(oldpkg.clean_pre(self.metadata, newpkg), False)

        # Apt -> nothing
        self.assertEqual(oldpkg.clean_pre(self.metadata, None), False)

    def test_clean_post(self):
        oldpkg = self.make_package('foo')
        newpkg = self.make_package(ConanPackage, 'foo',
                                   remote='foo/1.2.4@conan/stable')

        # Apt -> Conan
        self.assertEqual(oldpkg.clean_post(self.metadata, newpkg), False)

        # Apt -> nothing
        self.assertEqual(oldpkg.clean_post(self.metadata, None), False)

    def test_clean_all(self):
        oldpkg = self.make_package('foo')
        newpkg = self.make_package(ConanPackage, 'foo',
                                   remote='foo/1.2.4@conan/stable')

        # Apt -> Conan
        self.assertEqual(oldpkg.clean_all(self.metadata, newpkg),
                         (False, False))

        # Apt -> nothing
        self.assertEqual(oldpkg.clean_all(self.metadata, None), (False, False))

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

    def test_upgrade(self):
        opts = self.make_options()
        data = {'origin': 'apt', '_version': 0, 'name': 'foo',
                'remote': 'libfoo-dev', 'repository': None,
                'linkage': {'type': 'system', '_version': 0}}
        with mock.patch.object(AptPackage, 'upgrade',
                               side_effect=AptPackage.upgrade) as m:
            pkg = Package.rehydrate(data, _options=opts)
            self.assertIsInstance(pkg, AptPackage)
            m.assert_called_once()
