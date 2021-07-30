import os

from . import *


class TestUsage(IntegrationTest):
    name = 'usage'

    def assertUsageOutput(self, name, usage, extra_args=[], **kwargs):
        self.assertUsage(name, usage, extra_args, format='yaml')
        self.assertUsage(name, usage, extra_args, format='json')

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-tarball.yml')
        self.assertPopen(['mopack', 'resolve', config])

        # Usage for `hello`.
        expected_output_hello = {
            'name': 'hello',
            'type': 'pkg_config',
            'path': os.path.join(self.stage, 'mopack', 'build', 'hello',
                                 'pkgconfig'),
            'pcfiles': ['hello'],
            'extra_args': [],
        }
        self.assertUsageOutput('hello', expected_output_hello)
        self.assertUsageOutput('hello', expected_output_hello, ['--strict'])

        # Usage for `undef`.
        pkgconfdir = os.path.join(self.stage, 'mopack', 'pkgconfig')
        self.assertUsageOutput('undef', {
            'name': 'undef', 'type': 'system', 'path': pkgconfdir,
            'pcfiles': ['undef'], 'requirements': {
                'auto_link': False, 'headers': [], 'libraries': ['undef'],
            },
        }, extra_env={'PKG_CONFIG': 'nonexist'})
        self.assertCountEqual(
            call_pkg_config('undef', ['--cflags'], path=pkgconfdir), []
        )
        self.assertCountEqual(
            call_pkg_config('undef', ['--libs'], path=pkgconfdir), ['-lundef']
        )
        self.assertUsage('undef', extra_args=['--strict'], returncode=1)

        # Usage from wrong directory.
        wrongdir = stage_dir(self.name + '-wrongdir')
        pkgconfdir = os.path.join(wrongdir, 'mopack', 'pkgconfig')
        self.assertUsageOutput('hello', {
            'name': 'hello', 'type': 'system', 'path': pkgconfdir,
            'pcfiles': ['hello'], 'requirements': {
                'auto_link': False, 'headers': [], 'libraries': ['hello'],
            },
        }, ['--directory=' + wrongdir], extra_env={'PKG_CONFIG': 'nonexist'})
        self.assertCountEqual(
            call_pkg_config('hello', ['--cflags'], path=pkgconfdir), []
        )
        self.assertCountEqual(
            call_pkg_config('hello', ['--libs'], path=pkgconfdir), ['-lhello']
        )
        self.assertUsage('hello', extra_args=['--strict', '--directory=..'],
                         returncode=1)
