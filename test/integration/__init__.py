import json
import os
import subprocess
import tempfile
import unittest
import yaml

from .. import *

from mopack.iterutils import iterate, listify
from mopack.platforms import platform_name
from mopack.types import dependency_string


# Also supported: 'apt', 'mingw-cross'
test_features = {'boost', 'qt'}
for i in os.getenv('MOPACK_EXTRA_TESTS', '').split(' '):
    if i:
        test_features.add(i)
for i in os.getenv('MOPACK_SKIPPED_TESTS', '').split(' '):
    if i:
        test_features.remove(i)

# Get additional environment variables to use when getting usage. This
# is useful for setting things up to properly detect headers/libs for `path`
# usage.
usage_env = {}
try:
    test_env_file = os.path.join(test_dir, '../.mopack_test_env')
    with open(os.getenv('MOPACK_TEST_ENV_FILE', test_env_file)) as f:
        for line in f.readlines():
            k, v = line.rstrip('\n').split('=', 1)
            usage_env[k] = v
except FileNotFoundError:
    pass


def stage_dir(name, chdir=True):
    stage = tempfile.mkdtemp(prefix=name + '-', dir=test_stage_dir)
    if chdir:
        os.chdir(stage)
    return stage


def slurp(filename):
    with open(filename) as f:
        return f.read()


def cfg_common_options(*, strict=False, target_platform=platform_name(),
                       env=AlwaysEqual(), deploy_dirs={}):
    return {'_version': 1, 'strict': strict,
            'target_platform': target_platform, 'env': env,
            'deploy_dirs': deploy_dirs}


def cfg_bfg9000_options(toolchain=None):
    return {'type': 'bfg9000', '_version': 1, 'toolchain': toolchain}


def cfg_cmake_options(toolchain=None):
    return {'type': 'cmake', '_version': 1, 'toolchain': toolchain}


def cfg_conan_options(build=[], extra_args=[]):
    return {'origin': 'conan', '_version': 1, 'build': build,
            'extra_args': extra_args}


def cfg_options(**kwargs):
    result = {'common': cfg_common_options(**kwargs.pop('common', {})),
              'builders': [],
              'origins': []}
    for k, v in kwargs.items():
        opts = globals()['cfg_{}_options'.format(k)](**v)
        if k in ('bfg9000', 'cmake'):
            result['builders'].append(opts)
        else:
            result['origins'].append(opts)
    return result


def _cfg_package(origin, api_version, name, config_file, parent=None,
                 resolved=True, submodules=None, should_deploy=True):
    return {
        'origin': origin,
        '_version': api_version,
        'name': name,
        'config_file': config_file,
        'parent': parent,
        'resolved': resolved,
        'submodules': submodules,
        'should_deploy': should_deploy,
    }


def cfg_directory_pkg(name, config_file, *, path, builder, usage, **kwargs):
    result = _cfg_package('directory', 1, name, config_file, **kwargs)
    result.update({
        'path': path,
        'builder': builder,
        'usage': usage,
    })
    return result


def cfg_tarball_pkg(name, config_file, *, path=None, url=None, files=[],
                    srcdir=None, guessed_srcdir=None, patch=None, builder,
                    usage, **kwargs):
    result = _cfg_package('tarball', 1, name, config_file, **kwargs)
    result.update({
        'path': path,
        'url': url,
        'files': files,
        'srcdir': srcdir,
        'guessed_srcdir': guessed_srcdir,
        'patch': patch,
        'builder': builder,
        'usage': usage,
    })
    return result


def cfg_git_pkg(name, config_file, *, repository, rev, srcdir='.', builder,
                usage, **kwargs):
    result = _cfg_package('git', 1, name, config_file, **kwargs)
    result.update({
        'repository': repository,
        'rev': rev,
        'srcdir': srcdir,
        'builder': builder,
        'usage': usage,
    })
    return result


def cfg_apt_pkg(name, config_file, *, remote, repository=None, usage,
                **kwargs):
    result = _cfg_package('apt', 1, name, config_file, **kwargs)
    result.update({
        'remote': remote,
        'repository': repository,
        'usage': usage,
    })
    return result


def cfg_conan_pkg(name, config_file, *, remote, build=False, options={}, usage,
                  **kwargs):
    result = _cfg_package('conan', 1, name, config_file, **kwargs)
    result.update({
        'remote': remote,
        'build': build,
        'options': options,
        'usage': usage,
    })
    return result


def cfg_system_pkg(name, config_file, *, usage, **kwargs):
    result = _cfg_package('system', 1, name, config_file, **kwargs)
    result.update({
        'usage': usage,
    })
    return result


def cfg_bfg9000_builder(name, *, extra_args=[]):
    return {
        'type': 'bfg9000',
        '_version': 1,
        'name': name,
        'extra_args': extra_args,
    }


def cfg_cmake_builder(name, *, extra_args=[]):
    return {
        'type': 'cmake',
        '_version': 1,
        'name': name,
        'extra_args': extra_args,
    }


def cfg_custom_builder(name, *, build_commands=[], deploy_commands=[]):
    return {
        'type': 'custom',
        '_version': 1,
        'name': name,
        'build_commands': build_commands,
        'deploy_commands': deploy_commands,
    }


def _cfg_pkg_config_submodule_map(*, pcname=None):
    return {
        'pcname': pcname,
    }


def cfg_pkg_config_usage(*, pcname, pkg_config_path=None, submodule_map=None):
    if pkg_config_path is None:
        pkg_config_path = [{'base': 'builddir', 'path': 'pkgconfig'}]
    result = {
        'type': 'pkg_config',
        '_version': 1,
        'pcname': pcname,
        'pkg_config_path': pkg_config_path,
    }
    if submodule_map:
        if isinstance(submodule_map, dict):
            result['submodule_map'] = {k: _cfg_pkg_config_submodule_map(**v)
                                       for k, v in submodule_map.items()}
        else:
            result['submodule_map'] = submodule_map
    return result


def _cfg_path_submodule_map(*, dependencies=None, include_path=None,
                            library_path=None, headers=None, libraries=None,
                            compile_flags=None, link_flags=None):
    return {
        'dependencies': dependencies,
        'include_path': include_path,
        'library_path': library_path,
        'headers': headers,
        'libraries': libraries,
        'compile_flags': compile_flags,
        'link_flags': link_flags,
    }


def cfg_path_usage(*, auto_link=False, explicit_version=None, dependencies=[],
                   include_path=[], library_path=[], headers=[], libraries=[],
                   compile_flags=[], link_flags=[], submodule_map=None):
    result = {
        'type': 'path',
        '_version': 1,
        'auto_link': auto_link,
        'dependencies': dependencies,
        'explicit_version': explicit_version,
        'include_path': include_path,
        'library_path': library_path,
        'headers': headers,
        'libraries': libraries,
        'compile_flags': compile_flags,
        'link_flags': link_flags,
    }
    if submodule_map:
        if isinstance(submodule_map, dict):
            result['submodule_map'] = {k: _cfg_path_submodule_map(**v)
                                       for k, v in submodule_map.items()}
        else:
            result['submodule_map'] = submodule_map
    return result


def cfg_system_usage(*, pcname=None, **kwargs):
    result = cfg_path_usage(**kwargs)
    result.update({
        'type': 'system',
        'pcname': pcname
    })
    return result


class SubprocessError(unittest.TestCase.failureException):
    def __init__(self, returncode, env, message):
        envstr = ''.join('  {} = {}\n'.format(k, v)
                         for k, v in (env or {}).items())
        msg = 'returned {returncode}\n{env}{line}\n{msg}\n{line}'.format(
            returncode=returncode, env=envstr, line='-' * 60, msg=message
        )
        super().__init__(msg)


class SubprocessTestCase(unittest.TestCase):
    def assertExistence(self, path, exists):
        if os.path.exists(path) != exists:
            msg = '{!r} does not exist' if exists else '{!r} exists'
            raise unittest.TestCase.failureException(
                msg.format(os.path.normpath(path))
            )

    def assertExists(self, path):
        self.assertExistence(path, True)

    def assertNotExists(self, path):
        self.assertExistence(path, False)

    def assertPopen(self, command, *, env=None, extra_env=None, returncode=0):
        final_env = env if env is not None else os.environ
        if extra_env:
            final_env = final_env.copy()
            final_env.update(extra_env)

        proc = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            env=final_env, universal_newlines=True
        )
        if not (returncode == 'any' or
                (returncode == 'fail' and proc.returncode != 0) or
                proc.returncode in listify(returncode)):
            raise SubprocessError(proc.returncode, extra_env or env,
                                  proc.stdout)
        return proc.stdout

    def assertOutput(self, command, output, *args, **kwargs):
        self.assertEqual(self.assertPopen(command, *args, **kwargs), output)


class IntegrationTest(SubprocessTestCase):
    deploy = False

    def setUp(self):
        self.stage = stage_dir(self.name)
        self.pkgbuilddir = os.path.join(self.stage, 'mopack', 'build')
        if self.deploy:
            self.prefix = stage_dir(self.name + '-install', chdir=False)

    def assertUsage(self, name, usage='', extra_args=[], *, format='json',
                    submodules=[], extra_env=usage_env, returncode=0):
        loader = {
            'json': json.loads,
            'yaml': yaml.safe_load,
        }

        output = self.assertPopen((
            ['mopack', 'usage', dependency_string(name, submodules)] +
            (['--json'] if format == 'json' else []) +
            extra_args
        ), extra_env=extra_env, returncode=returncode)
        if returncode == 0:
            self.assertEqual(loader[format](output), usage)
        return output

    def assertPkgConfigUsage(self, name, submodules=[], *, type='pkg_config',
                             pcnames=None, pkg_config_path=['pkgconfig']):
        pkg_config_path = [(i if os.path.isabs(i) else
                            os.path.join(self.pkgbuilddir, name, i))
                           for i in pkg_config_path]
        if pcnames is None:
            pcnames = [name]

        self.assertUsage(name, {
            'name': dependency_string(name, submodules), 'type': type,
            'pcnames': pcnames, 'pkg_config_path': pkg_config_path,
        }, submodules=submodules)

    def assertPathUsage(self, name, submodules=[], *, type='path', version='',
                        auto_link=False, pcnames=None, include_path=[],
                        library_path=[], libraries=None, compile_flags=[],
                        link_flags=[]):
        if libraries is None:
            libraries = [name]
        if pcnames is None:
            pcnames = ([dependency_string(name, [i]) for i in
                        iterate(submodules)] if submodules else [name])

        pkgconfdir = os.path.join(self.stage, 'mopack', 'pkgconfig')
        self.assertUsage(name, {
            'name': dependency_string(name, submodules), 'type': type,
            'generated': True, 'auto_link': auto_link, 'pcnames': pcnames,
            'pkg_config_path': [pkgconfdir],
        }, submodules=submodules)

        if not isinstance(include_path, AlwaysEqual):
            self.assertCountEqual(
                call_pkg_config(pcnames, ['--cflags-only-I'], path=pkgconfdir),
                ['-I' + i for i in include_path]
            )
        if not isinstance(library_path, AlwaysEqual):
            self.assertCountEqual(
                call_pkg_config(pcnames, ['--libs-only-L'], path=pkgconfdir),
                ['-L' + i for i in library_path]
            )
        if not isinstance(libraries, AlwaysEqual):
            self.assertCountEqual(
                call_pkg_config(pcnames, ['--libs-only-l'], path=pkgconfdir),
                ['-l' + i for i in libraries]
            )
        if not isinstance(compile_flags, AlwaysEqual):
            self.assertCountEqual(
                call_pkg_config(pcnames, ['--cflags-only-other'],
                                path=pkgconfdir),
                compile_flags
            )
        if not isinstance(link_flags, AlwaysEqual):
            self.assertCountEqual(
                call_pkg_config(pcnames, ['--libs-only-other'],
                                path=pkgconfdir),
                link_flags
            )

        self.assertEqual(
            call_pkg_config(pcnames, ['--modversion'], path=pkgconfdir,
                            split=False),
            version
        )
