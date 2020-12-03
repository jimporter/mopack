import json
import os
import yaml

from . import *


class TestUsage(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('usage')

    def assertUsage(self, *args, **kwargs):
        return self.assertPopen(['mopack', 'usage', *args], **kwargs)

    def assertUsageOutput(self, name, expected, extra_args=[], **kwargs):
        output = yaml.safe_load(self.assertUsage(name, *extra_args, **kwargs))
        self.assertEqual(output, expected)

        output = json.loads(self.assertUsage(name, '--json', *extra_args,
                                             **kwargs))
        self.assertEqual(output, expected)

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-tarball.yml')
        self.assertPopen(['mopack', 'resolve', config])

        # Usage for `hello`.
        expected_output_hello = {
            'name': 'hello',
            'type': 'pkg-config',
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
        self.assertUsage('undef', '--strict', returncode=1)

        # Usage from wrong directory.
        self.assertUsageOutput('hello', {
            'name': 'hello', 'type': 'path', 'auto_link': False,
            'include_path': [], 'library_path': [], 'headers': [],
            'libraries': ['hello'], 'compile_flags': [], 'link_flags': [],
        }, ['--directory=..'], extra_env={'PKG_CONFIG': 'nonexist'})
        self.assertUsage('hello', '--strict', '--directory=..', returncode=1)
