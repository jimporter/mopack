import os

from . import *


class TestUsage(IntegrationTest):
    name = 'usage'

    def assertUsageOutput(self, name, usage, extra_args=[], **kwargs):
        self.assertUsage(name, usage, extra_args, format='yaml', **kwargs)
        self.assertUsage(name, usage, extra_args, format='json', **kwargs)

    def test_resolve(self):
        test_lib_dir = os.path.join(test_data_dir, 'libdir')
        usage_env = {'MOPACK_LIB_NAMES': 'lib{}.so',
                     'MOPACK_LIB_PATH': test_lib_dir}

        config = os.path.join(test_data_dir, 'mopack-tarball.yml')
        self.assertPopen(['mopack', '--debug', 'resolve', config])

        # Usage for `hello`.
        expected_output_hello = {
            'name': 'hello',
            'type': 'pkg_config',
            'path': [os.path.join(self.stage, 'mopack', 'build', 'hello',
                                  'pkgconfig')],
            'pcfiles': ['hello'],
            'extra_args': [],
        }
        self.assertUsageOutput('hello', expected_output_hello)
        self.assertUsageOutput('hello', expected_output_hello, ['--strict'])

        # Usage for `fake`.
        pkgconfdir = os.path.join(self.stage, 'mopack', 'pkgconfig')
        self.assertUsageOutput('fake', {
            'name': 'fake', 'type': 'system', 'generated': True,
            'auto_link': False, 'path': [pkgconfdir], 'pcfiles': ['fake'],
        }, extra_env=usage_env)
        self.assertCountEqual(
            call_pkg_config('fake', ['--cflags'], path=pkgconfdir), []
        )
        self.assertCountEqual(
            call_pkg_config('fake', ['--libs'], path=pkgconfdir),
            ['-L' + test_lib_dir, '-lfake']
        )
        self.assertUsage('fake', extra_args=['--strict'], returncode=1)

        # Usage from wrong directory.
        wrongdir = stage_dir(self.name + '-wrongdir')
        wrongdir_args = ['--directory=' + wrongdir]
        pkgconfdir = os.path.join(wrongdir, 'mopack', 'pkgconfig')
        self.assertUsage('hello', extra_args=wrongdir_args,
                         format='yaml', returncode=1)
        output = self.assertUsage('hello', extra_args=wrongdir_args,
                                  returncode=1)
        self.assertEqual(json.loads(output),
                         {'error': "unable to find library 'hello'"})
        self.assertUsageOutput('fake', {
            'name': 'fake', 'type': 'system', 'generated': True,
            'auto_link': False, 'path': [pkgconfdir], 'pcfiles': ['fake'],
        }, wrongdir_args, extra_env=usage_env)
        self.assertCountEqual(
            call_pkg_config('fake', ['--cflags'], path=pkgconfdir), []
        )
        self.assertCountEqual(
            call_pkg_config('fake', ['--libs'], path=pkgconfdir),
            ['-L' + test_lib_dir, '-lfake']
        )
        self.assertUsage('fake', extra_args=['--strict'] + wrongdir_args,
                         returncode=1)
