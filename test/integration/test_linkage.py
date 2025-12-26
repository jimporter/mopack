import os

from . import *


class TestLinkage(IntegrationTest):
    name = 'linkage'

    def assertLinkageOutput(self, name, linkage, extra_args=[], **kwargs):
        self.assertLinkage(name, linkage, extra_args, format='yaml', **kwargs)
        self.assertLinkage(name, linkage, extra_args, format='json', **kwargs)

    def test_resolve(self):
        test_lib_dir = os.path.join(test_data_dir, 'libdir')
        linkage_env = {'MOPACK_LIB_NAMES': 'lib{}.so',
                       'MOPACK_LIB_PATH': test_lib_dir}

        config = os.path.join(test_data_dir, 'mopack-tarball.yml')
        self.assertPopen(mopack_cmd('--debug', 'resolve', config))

        # Linkage for `hello`.
        expected_output_hello = {
            'name': 'hello',
            'type': 'pkg_config',
            'pcnames': ['hello'],
            'pkg_config_path': [os.path.join(self.stage, 'mopack', 'build',
                                             'hello', 'pkgconfig')],
        }
        self.assertLinkageOutput('hello', expected_output_hello)
        self.assertLinkageOutput('hello', expected_output_hello, ['--strict'])

        # Linkage for `fake`.
        pkgconfdir = os.path.join(self.stage, 'mopack', 'pkgconfig')
        self.assertLinkageOutput('fake', {
            'name': 'fake', 'type': 'system', 'pcnames': ['fake'],
            'pkg_config_path': [pkgconfdir],
        }, extra_env=linkage_env)
        self.assertCountEqual(
            call_pkg_config('fake', ['--cflags'], path=pkgconfdir), []
        )
        self.assertCountEqual(
            call_pkg_config('fake', ['--libs'], path=pkgconfdir),
            ['-L' + test_lib_dir, '-lfake']
        )
        self.assertLinkage('fake', extra_args=['--strict'], returncode=1)

        # Linkage from wrong directory.
        wrongdir = stage_dir(self.name + '-wrongdir')
        wrongdir_args = ['--directory=' + wrongdir]
        pkgconfdir = os.path.join(wrongdir, 'mopack', 'pkgconfig')
        self.assertLinkage('hello', extra_args=wrongdir_args,
                           format='yaml', returncode=1)
        output = self.assertLinkage('hello', extra_args=wrongdir_args,
                                    returncode=1)
        self.assertEqual(json.loads(output),
                         {'error': "unable to find library 'hello'"})
        self.assertLinkageOutput('fake', {
            'name': 'fake', 'type': 'system', 'pcnames': ['fake'],
            'pkg_config_path': [pkgconfdir],
        }, wrongdir_args, extra_env=linkage_env)
        self.assertCountEqual(
            call_pkg_config('fake', ['--cflags'], path=pkgconfdir), []
        )
        self.assertCountEqual(
            call_pkg_config('fake', ['--libs'], path=pkgconfdir),
            ['-L' + test_lib_dir, '-lfake']
        )
        self.assertLinkage('fake', extra_args=['--strict'] + wrongdir_args,
                           returncode=1)

    def test_resolve_strict(self):
        config = os.path.join(test_data_dir, 'mopack-tarball.yml')
        self.assertPopen(mopack_cmd('resolve', '--strict', config))

        # Linkage for `hello`.
        expected_output_hello = {
            'name': 'hello',
            'type': 'pkg_config',
            'pcnames': ['hello'],
            'pkg_config_path': [os.path.join(self.stage, 'mopack', 'build',
                                             'hello', 'pkgconfig')],
        }
        self.assertLinkageOutput('hello', expected_output_hello)
        self.assertLinkageOutput('hello', expected_output_hello, ['--strict'])

        # Linkage for `fake`.
        self.assertLinkage('fake', returncode=1)
        self.assertLinkage('fake', extra_args=['--strict'], returncode=1)
