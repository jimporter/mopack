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
        self.assertUsageOutput('undef', {
            'name': 'undef', 'type': 'path', 'auto_link': False,
            'include_path': [], 'library_path': [], 'headers': [],
            'libraries': ['undef'], 'compile_flags': [], 'link_flags': [],
        }, extra_env={'PKG_CONFIG': 'nonexist'})
        self.assertUsage('undef', extra_args=['--strict'], returncode=1)

        # Usage from wrong directory.
        self.assertUsageOutput('hello', {
            'name': 'hello', 'type': 'path', 'auto_link': False,
            'include_path': [], 'library_path': [], 'headers': [],
            'libraries': ['hello'], 'compile_flags': [], 'link_flags': [],
        }, ['--directory=..'], extra_env={'PKG_CONFIG': 'nonexist'})
        self.assertUsage('hello', extra_args=['--strict', '--directory=..'],
                         returncode=1)
