import os
import subprocess
from unittest import mock

from . import *
from ... import assert_logging, rehydrate_kwargs
from .... import *

from mopack.builders.bfg9000 import Bfg9000Builder
from mopack.builders.none import NoneBuilder
from mopack.config import Config
from mopack.linkages.path_system import SystemLinkage
from mopack.origins import Package
from mopack.origins.apt import AptPackage
from mopack.origins.sdist import GitPackage
from mopack.types import ConfigurationError


def mock_exists(p):
    return os.path.basename(p) == 'mopack.yml'


class TestGit(SDistTestCase):
    pkg_type = GitPackage
    srcurl = 'https://github.com/user/repo.git'
    srcssh = 'git@github.com:user/repo.git'

    def setUp(self):
        super().setUp()
        self.config = Config([])

    def check_fetch(self, pkg):
        srcdir = os.path.join(self.pkgdir, 'src', 'foo')
        git_cmds = [['git', 'clone', pkg.repository, srcdir]]
        if pkg.rev[0] in ['branch', 'tag']:
            git_cmds[0].extend(['--branch', pkg.rev[1]])
        else:
            git_cmds.append(['git', 'checkout', pkg.rev[1]])

        with mock_open_log(), \
             mock.patch('mopack.origins.sdist.pushd'), \
             mock.patch('mopack.log.LogFile.check_call') as mcall:
            with assert_logging([('fetch',
                                  'foo from {}'.format(pkg.repository))]):
                pkg.fetch(self.metadata, self.config)
            mcall.assert_has_calls([mock.call(i, env={}) for i in git_cmds],
                                   any_order=True)

    def test_url(self):
        pkg = self.make_package('foo', repository=self.srcurl, build='bfg9000')
        builder = self.make_builder(Bfg9000Builder, pkg)
        self.assertEqual(pkg.repository, self.srcurl)
        self.assertEqual(pkg.rev, ['branch', 'master'])
        self.assertEqual(pkg.srcdir, '.')
        self.assertEqual(pkg.builders, [builder])
        self.assertEqual(pkg.needs_dependencies, True)
        self.assertEqual(pkg.should_deploy, True)

        self.check_fetch(pkg)
        self.check_resolve(pkg)

    def test_path(self):
        pkg = self.make_package('foo', repository=self.srcssh, build='bfg9000')
        builder = self.make_builder(Bfg9000Builder, pkg)
        self.assertEqual(pkg.repository, self.srcssh)
        self.assertEqual(pkg.rev, ['branch', 'master'])
        self.assertEqual(pkg.srcdir, '.')
        self.assertEqual(pkg.builders, [builder])
        self.assertEqual(pkg.needs_dependencies, True)
        self.assertEqual(pkg.should_deploy, True)

        self.check_fetch(pkg)
        self.check_resolve(pkg)

    def test_tag(self):
        pkg = self.make_package('foo', repository=self.srcssh, tag='v1.0',
                                build='bfg9000')
        builder = self.make_builder(Bfg9000Builder, pkg)
        self.assertEqual(pkg.repository, self.srcssh)
        self.assertEqual(pkg.rev, ['tag', 'v1.0'])
        self.assertEqual(pkg.srcdir, '.')
        self.assertEqual(pkg.builders, [builder])
        self.assertEqual(pkg.needs_dependencies, True)
        self.assertEqual(pkg.should_deploy, True)

        self.check_fetch(pkg)
        self.check_resolve(pkg)

    def test_branch(self):
        pkg = self.make_package('foo', repository=self.srcssh,
                                branch='mybranch', build='bfg9000')
        builder = self.make_builder(Bfg9000Builder, pkg)
        self.assertEqual(pkg.repository, self.srcssh)
        self.assertEqual(pkg.rev, ['branch', 'mybranch'])
        self.assertEqual(pkg.srcdir, '.')
        self.assertEqual(pkg.builders, [builder])
        self.assertEqual(pkg.needs_dependencies, True)
        self.assertEqual(pkg.should_deploy, True)

        self.check_fetch(pkg)
        self.check_resolve(pkg)

    def test_commit(self):
        pkg = self.make_package('foo', repository=self.srcssh,
                                commit='abcdefg', build='bfg9000')
        builder = self.make_builder(Bfg9000Builder, pkg)
        self.assertEqual(pkg.repository, self.srcssh)
        self.assertEqual(pkg.rev, ['commit', 'abcdefg'])
        self.assertEqual(pkg.srcdir, '.')
        self.assertEqual(pkg.builders, [builder])
        self.assertEqual(pkg.needs_dependencies, True)
        self.assertEqual(pkg.should_deploy, True)

        self.check_fetch(pkg)
        self.check_resolve(pkg)

    def test_invalid_tag_branch_commit(self):
        with self.assertRaises(TypeError):
            self.make_package('foo', repository=self.srcssh, tag='v1.0',
                              branch='mybranch', build='bfg9000')
        with self.assertRaises(TypeError):
            self.make_package('foo', repository=self.srcssh, tag='v1.0',
                              commit='abcdefg', build='bfg9000')
        with self.assertRaises(TypeError):
            self.make_package('foo', repository=self.srcssh,
                              branch='mybranch', commit='abcdefg',
                              build='bfg9000')
        with self.assertRaises(TypeError):
            self.make_package('foo', repository=self.srcssh, tag='v1.0',
                              branch='mybranch', commit='abcdefg',
                              build='bfg9000')

    def test_srdir(self):
        pkg = self.make_package('foo', repository=self.srcssh, srcdir='dir',
                                build='bfg9000')
        builder = self.make_builder(Bfg9000Builder, pkg)
        self.assertEqual(pkg.repository, self.srcssh)
        self.assertEqual(pkg.rev, ['branch', 'master'])
        self.assertEqual(pkg.srcdir, 'dir')
        self.assertEqual(pkg.builders, [builder])

        self.check_fetch(pkg)
        self.check_resolve(pkg)

    def test_build(self):
        build = {'type': 'bfg9000', 'extra_args': '--extra'}
        pkg = self.make_package('foo', repository=self.srcssh, build=build,
                                linkage='pkg_config')
        builder = self.make_builder(Bfg9000Builder, pkg, extra_args='--extra')
        self.assertEqual(pkg.repository, self.srcssh)
        self.assertEqual(pkg.rev, ['branch', 'master'])
        self.assertEqual(pkg.srcdir, '.')
        self.assertEqual(pkg.builders, [builder])

        self.check_fetch(pkg)
        self.check_resolve(pkg)

    def test_infer_build(self):
        # Basic inference
        pkg = self.make_package('foo', repository=self.srcssh)
        self.assertEqual(pkg.builders, None)

        with mock_open_log(), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('mopack.log.LogFile.check_call'), \
             mock.patch('builtins.open', mock_open_after_first(
                 read_data='export:\n  build: bfg9000'
             )):
            with assert_logging([('fetch',
                                  'foo from {}'.format(pkg.repository))]):
                config = pkg.fetch(self.metadata, self.config)
            self.assertEqual(config.export.build, 'bfg9000')
            self.assertEqual(pkg, self.make_package(
                'foo', repository=self.srcssh, build='bfg9000'
            ))
        self.check_resolve(pkg)

        # Infer but override linkage and version
        pkg = self.make_package('foo', repository=self.srcssh,
                                linkage={'type': 'system'})
        self.assertEqual(pkg.builders, None)

        with mock_open_log(), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('mopack.log.LogFile.check_call'), \
             mock.patch('builtins.open', mock_open_after_first(
                 read_data='export:\n  build: bfg9000'
             )):
            with assert_logging([('fetch',
                                  'foo from {}'.format(pkg.repository))]):
                config = pkg.fetch(self.metadata, self.config)
            self.assertEqual(config.export.build, 'bfg9000')
            self.assertEqual(pkg, self.make_package(
                'foo', repository=self.srcssh, build='bfg9000',
                linkage={'type': 'system'}
            ))
        with mock.patch('mopack.log.LogFile.check_call',
                        side_effect=OSError()), \
             mock.patch('mopack.linkages.path_system.PathLinkage._filter_path',
                        lambda *args: []), \
             mock.patch('mopack.linkages.path_system.file_outdated',
                        return_value=True), \
             mock.patch('os.makedirs'), \
             mock.patch('builtins.open'):
            self.check_resolve(pkg, linkage={
                'name': 'foo', 'type': 'system', 'generated': True,
                'auto_link': False, 'pcnames': ['foo'],
                'pkg_config_path': [self.pkgconfdir(None)],
            })

    def test_infer_build_override(self):
        pkg = self.make_package('foo', repository=self.srcssh, build='cmake',
                                linkage='pkg_config')

        with mock_open_log(), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('mopack.log.LogFile.check_call'), \
             mock.patch('builtins.open', mock_open_after_first(
                 read_data='export:\n  build: bfg9000'
             )):
            with assert_logging([('fetch',
                                  'foo from {}'.format(pkg.repository))]):
                config = pkg.fetch(self.metadata, self.config)
            self.assertEqual(config.export.build, 'bfg9000')
            self.assertEqual(pkg, self.make_package(
                'foo', repository=self.srcssh, build='cmake',
                linkage='pkg_config'
            ))
        with mock.patch('mopack.builders.cmake.pushd'):
            self.check_resolve(pkg)

    def test_linkage(self):
        pkg = self.make_package('foo', repository=self.srcssh, build='bfg9000',
                                linkage='pkg_config')
        builder = self.make_builder(Bfg9000Builder, pkg)
        self.assertEqual(pkg.repository, self.srcssh)
        self.assertEqual(pkg.rev, ['branch', 'master'])
        self.assertEqual(pkg.srcdir, '.')
        self.assertEqual(pkg.builders, [builder])

        self.check_fetch(pkg)
        self.check_resolve(pkg)

        with mock.patch('subprocess.run') as mrun:
            pkg.version(self.metadata)
            mrun.assert_called_once_with(
                ['pkg-config', 'foo', '--modversion'],
                check=True, env={'PKG_CONFIG_PATH': self.pkgconfdir('foo')},
                stdout=subprocess.PIPE, universal_newlines=True
            )

        linkage = {'type': 'pkg_config', 'pkg_config_path': 'pkgconf'}
        pkg = self.make_package('foo', repository=self.srcssh, build='bfg9000',
                                linkage=linkage)
        self.assertEqual(pkg.repository, self.srcssh)
        self.assertEqual(pkg.rev, ['branch', 'master'])
        self.assertEqual(pkg.srcdir, '.')
        self.assertEqual(pkg.builders, [builder])

        self.check_fetch(pkg)
        self.check_resolve(pkg, linkage={
            'name': 'foo', 'type': 'pkg_config', 'pcnames': ['foo'],
            'pkg_config_path': [self.pkgconfdir('foo', 'pkgconf')],
        })

        linkage = {'type': 'path', 'libraries': []}
        pkg = self.make_package('foo', repository=self.srcssh, build='bfg9000',
                                linkage=linkage)
        self.assertEqual(pkg.repository, self.srcssh)
        self.assertEqual(pkg.rev, ['branch', 'master'])
        self.assertEqual(pkg.srcdir, '.')
        self.assertEqual(pkg.builders, [builder])

        self.check_fetch(pkg)
        self.check_resolve(pkg, linkage={
            'name': 'foo', 'type': 'path', 'generated': True,
            'auto_link': False, 'pcnames': ['foo'],
            'pkg_config_path': [self.pkgconfdir(None)],
        })

        with mock.patch('subprocess.run') as mrun:
            self.assertEqual(pkg.version(self.metadata), None)
            mrun.assert_not_called()

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        pkg = self.make_package('foo', repository=self.srcssh, build='bfg9000',
                                submodules=submodules_required)
        self.check_fetch(pkg)
        self.check_resolve(pkg, submodules=['sub'])

        pkg = self.make_package(
            'foo', repository=self.srcssh, build='bfg9000',
            linkage={'type': 'pkg_config', 'pcname': 'bar'},
            submodules=submodules_required
        )
        self.check_fetch(pkg)
        self.check_resolve(pkg, submodules=['sub'], linkage={
            'name': 'foo[sub]', 'type': 'pkg_config',
            'pcnames': ['bar', 'foo_sub'],
            'pkg_config_path': [self.pkgconfdir('foo')],
        })

        pkg = self.make_package('foo', repository=self.srcssh, build='bfg9000',
                                submodules=submodules_optional)
        self.check_fetch(pkg)
        self.check_resolve(pkg, submodules=['sub'])

        pkg = self.make_package(
            'foo', repository=self.srcssh, build='bfg9000',
            linkage={'type': 'pkg_config', 'pcname': 'bar'},
            submodules=submodules_optional
        )
        self.check_fetch(pkg)
        self.check_resolve(pkg, submodules=['sub'], linkage={
            'name': 'foo[sub]', 'type': 'pkg_config',
            'pcnames': ['bar', 'foo_sub'],
            'pkg_config_path': [self.pkgconfdir('foo')],
        })

    def test_invalid_submodule(self):
        pkg = self.make_package(
            'foo', repository=self.srcssh, build='bfg9000',
            submodules={'names': ['sub'], 'required': True}
        )
        with self.assertRaises(ValueError):
            pkg.get_linkage(self.metadata, ['invalid'])

    def test_already_fetched_branch(self):
        def mock_exists(p):
            return os.path.basename(p) == 'foo'

        pkg = self.make_package('foo', repository=self.srcssh, build='bfg9000')
        with mock_open_log(), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('mopack.origins.sdist.pushd'), \
             mock.patch('mopack.log.LogFile.check_call') as mcall:
            with assert_logging([]):
                pkg.fetch(self.metadata, self.config)
            mcall.assert_called_once_with(['git', 'pull'], env={})
        self.check_resolve(pkg)

    def test_already_fetched_tag(self):
        def mock_exists(p):
            return os.path.basename(p) == 'foo'

        pkg = self.make_package('foo', repository=self.srcssh, tag='v1.0',
                                build='bfg9000')
        with mock_open_log(), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('mopack.origins.sdist.pushd'), \
             mock.patch('subprocess.run') as mrun:
            with assert_logging([]):
                pkg.fetch(self.metadata, self.config)
            mrun.assert_not_called()
        self.check_resolve(pkg)

    def test_already_fetched_commit(self):
        def mock_exists(p):
            return os.path.basename(p) == 'foo'

        pkg = self.make_package('foo', repository=self.srcssh,
                                commit='abcdefg', build='bfg9000')
        with mock_open_log(), \
             mock.patch('os.path.exists', mock_exists), \
             mock.patch('mopack.origins.sdist.pushd'), \
             mock.patch('subprocess.run') as mrun:
            with assert_logging([]):
                pkg.fetch(self.metadata, self.config)
            mrun.assert_not_called()
        self.check_resolve(pkg)

    def test_deploy(self):
        deploy_dirs = {'prefix': '/usr/local'}
        pkg = self.make_package('foo', repository=self.srcssh, build='bfg9000',
                                deploy_dirs=deploy_dirs)
        self.assertEqual(pkg.should_deploy, True)

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('mopack.builders.ninja.pushd'), \
             mock.patch('mopack.log.LogFile.check_call') as mcall:
            with assert_logging([('resolve', 'foo')]):
                pkg.resolve(self.metadata)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'foo.log'
            ), 'a')
            builddir = os.path.join(self.pkgdir, 'build', 'foo')
            mcall.assert_any_call(
                ['bfg9000', 'configure', builddir, '--prefix', '/usr/local'],
                env={}
            )

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('mopack.builders.ninja.pushd'), \
             mock.patch('mopack.log.LogFile.check_call') as mcall:
            with assert_logging([('deploy', 'foo')]):
                pkg.deploy(self.metadata)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'deploy', 'foo.log'
            ), 'a')
            mcall.assert_any_call(['ninja', 'install'], env={})

        pkg = self.make_package('foo', repository=self.srcssh, build='bfg9000',
                                deploy=False)
        self.assertEqual(pkg.should_deploy, False)

        with mock_open_log() as mopen:
            pkg.deploy(self.metadata)
            mopen.assert_not_called()

    def test_clean_pre(self):
        otherssh = 'git@github.com:user/other.git'

        oldpkg = self.make_package('foo', repository=self.srcssh,
                                   build='bfg9000')
        newpkg1 = self.make_package('foo', repository=otherssh,
                                    build='bfg9000')
        newpkg2 = self.make_package(AptPackage, 'foo')

        srcdir = os.path.join(self.pkgdir, 'src', 'foo')

        # Git -> Git (same)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch('shutil.rmtree') as mrmtree:
            self.assertEqual(oldpkg.clean_pre(self.metadata, oldpkg), False)
            mlog.assert_not_called()
            mrmtree.assert_not_called()

        # Git -> Git (different)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch('shutil.rmtree') as mrmtree:
            self.assertEqual(oldpkg.clean_pre(self.metadata, newpkg1), True)
            mlog.assert_called_once()
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

        # Git -> Apt
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch('shutil.rmtree') as mrmtree:
            self.assertEqual(oldpkg.clean_pre(self.metadata, newpkg2), True)
            mlog.assert_called_once()
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

        # Git -> nothing
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch('shutil.rmtree') as mrmtree:
            self.assertEqual(oldpkg.clean_pre(self.metadata, None), True)
            mlog.assert_called_once()
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

        # Git -> nothing (quiet)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch('shutil.rmtree') as mrmtree:
            self.assertEqual(oldpkg.clean_pre(self.metadata, None, True), True)
            mlog.assert_not_called()
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

    def test_clean_post(self):
        otherssh = 'git@github.com:user/other.git'

        oldpkg = self.make_package('foo', repository=self.srcssh,
                                   build='bfg9000')
        newpkg1 = self.make_package('foo', repository=otherssh,
                                    build='bfg9000')
        newpkg2 = self.make_package(AptPackage, 'foo')

        # Git -> Git (same)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:
            self.assertEqual(oldpkg.clean_post(self.metadata, oldpkg), False)
            mlog.assert_not_called()
            mclean.assert_not_called()

        # Git -> Git (different)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:
            self.assertEqual(oldpkg.clean_post(self.metadata, newpkg1), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.metadata, oldpkg)

        # Git -> Apt
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:
            self.assertEqual(oldpkg.clean_post(self.metadata, newpkg2), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.metadata, oldpkg)

        # Git -> nothing
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean:
            self.assertEqual(oldpkg.clean_post(self.metadata, None), True)
            mlog.assert_called_once()
            mclean.assert_called_once_with(self.metadata, oldpkg)

    def test_clean_all(self):
        otherssh = 'git@github.com:user/other.git'

        oldpkg = self.make_package('foo', repository=self.srcssh,
                                   build='bfg9000')
        newpkg1 = self.make_package('foo', repository=otherssh,
                                    build='bfg9000')
        newpkg2 = self.make_package(AptPackage, 'foo')

        srcdir = os.path.join(self.pkgdir, 'src', 'foo')

        # Git -> Git (same)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean, \
             mock.patch('shutil.rmtree') as mrmtree:
            self.assertEqual(oldpkg.clean_all(self.metadata, oldpkg),
                             (False, False))
            mlog.assert_not_called()
            mclean.assert_not_called()
            mrmtree.assert_not_called()

        # Git -> Git (different)
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean, \
             mock.patch('shutil.rmtree') as mrmtree:
            self.assertEqual(oldpkg.clean_all(self.metadata, newpkg1),
                             (True, True))
            self.assertEqual(mlog.call_count, 2)
            mclean.assert_called_once_with(self.metadata, oldpkg)
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

        # Git -> Apt
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean, \
             mock.patch('shutil.rmtree') as mrmtree:
            self.assertEqual(oldpkg.clean_all(self.metadata, newpkg2),
                             (True, True))
            self.assertEqual(mlog.call_count, 2)
            mclean.assert_called_once_with(self.metadata, oldpkg)
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

        # Git -> nothing
        with mock.patch('mopack.log.pkg_clean') as mlog, \
             mock.patch(mock_bfgclean) as mclean, \
             mock.patch('shutil.rmtree') as mrmtree:
            self.assertEqual(oldpkg.clean_all(self.metadata, None),
                             (True, True))
            self.assertEqual(mlog.call_count, 2)
            mclean.assert_called_once_with(self.metadata, oldpkg)
            mrmtree.assert_called_once_with(srcdir, ignore_errors=True)

    def test_equality(self):
        pkg = self.make_package('foo', repository=self.srcssh, build='bfg9000')

        self.assertEqual(pkg, self.make_package(
            'foo', repository=self.srcssh, build='bfg9000'
        ))
        self.assertEqual(pkg, self.make_package(
            'foo', repository=self.srcssh, build='bfg9000',
            config_file='/path/to/mopack2.yml'
        ))

        self.assertNotEqual(pkg, self.make_package(
            'bar', repository=self.srcssh, build='bfg9000',
        ))
        self.assertNotEqual(pkg, self.make_package(
            'foo', repository=self.srcurl, build='bfg9000',
        ))

    def test_rehydrate(self):
        opts = self.make_options()
        pkg = GitPackage('foo', repository=self.srcssh, build='bfg9000',
                         _options=opts, config_file=self.config_file)
        data = through_json(pkg.dehydrate())
        self.assertEqual(pkg, Package.rehydrate(
            data, _options=opts, **rehydrate_kwargs
        ))

        pkg = GitPackage('foo', repository=self.srcssh, _options=opts,
                         config_file=self.config_file)
        with self.assertRaises(ConfigurationError):
            data = pkg.dehydrate()

    def test_upgrade(self):
        opts = self.make_options()
        data = {
            'origin': 'git', '_version': 0, 'name': 'foo',
            'repository': 'repo', 'tag': None, 'branch': None, 'commit': None,
            'srcdir': '.',
            'builder': {'type': 'none', '_version': 1, 'name': 'foo'},
            'linkage': {'type': 'system', '_version': 1},
        }
        with mock.patch.object(GitPackage, 'upgrade',
                               side_effect=GitPackage.upgrade) as m:
            pkg = Package.rehydrate(data, _options=opts, **rehydrate_kwargs)
            self.assertIsInstance(pkg, GitPackage)
            self.assertIsInstance(pkg.linkage, SystemLinkage)
            self.assertEqual([type(i) for i in pkg.builders], [NoneBuilder])
            m.assert_called_once()

    def test_builder_types(self):
        pkg = GitPackage('foo', repository=self.srcssh, build='bfg9000',
                         _options=self.make_options(),
                         config_file=self.config_file)
        self.assertEqual(pkg.builder_types, ['bfg9000'])

        pkg = GitPackage('foo', repository=self.srcssh,
                         _options=self.make_options(),
                         config_file=self.config_file)
        with self.assertRaises(ConfigurationError):
            pkg.builder_types
