import os

from . import *


class TestLinkage(IntegrationTest):
    name = 'linkage'

    def assertLinkageOutput(self, name, linkage, extra_args=[], **kwargs):
        self.assertLinkage(name, linkage, extra_args, format='yaml', **kwargs)
        self.assertLinkage(name, linkage, extra_args, format='json', **kwargs)

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-tarball.yml')
        self.assertResolve(config)

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

        # Linkage from wrong directory.
        wrongdir = stage_dir(self.name + '-wrongdir')
        wrongdir_args = ['--directory=' + wrongdir]
        output = self.assertLinkage('hello', extra_args=wrongdir_args,
                                    returncode=1)
        self.assertRegex(json.loads(output)['error'],
                         "^unable to find library 'hello'")

    def test_resolve_fake(self):
        test_lib_dir = os.path.join(test_data_dir, 'libdir')
        test_env = {'MOPACK_LIB_NAMES': 'lib{}.so',
                    'MOPACK_LIB_PATH': test_lib_dir}

        config = os.path.join(test_data_dir, 'mopack-tarball.yml')
        self.assertResolve(config, extra_env=test_env)

        # Linkage for `fake`.
        pkgconfdir = os.path.join(self.stage, 'mopack', 'pkgconfig')
        self.assertLinkageOutput('fake', {
            'name': 'fake', 'type': 'system', 'pcnames': ['fake'],
            'pkg_config_path': [pkgconfdir],
        })
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
        output = self.assertLinkage('fake', extra_args=wrongdir_args,
                                    returncode=1)
        self.assertRegex(json.loads(output)['error'],
                         "^unable to find library 'fake'")

    def test_resolve_strict(self):
        config = os.path.join(test_data_dir, 'mopack-tarball.yml')
        self.assertResolve(config, ['--strict'])

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

        # Linkage for `missing`.
        self.assertLinkage('missing', returncode=1)
        self.assertLinkage('missing', extra_args=['--strict'], returncode=1)
