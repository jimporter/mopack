import json
import os
import yaml

from . import *


class TestUsage(IntegrationTest):
    def setUp(self):
        self.stage = stage_dir('usage')

    def assertUsage(self, *args, **kwargs):
        return self.assertPopen(['mopack', 'usage', *args], **kwargs)

    def assertUsageOutput(self, name, expected, extra_args=[]):
        output = yaml.safe_load(self.assertUsage(name, *extra_args))
        self.assertEqual(output, expected)

        output = json.loads(self.assertUsage(name, '--json', *extra_args))
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
            'pcfiles': ['hello']
        }
        self.assertUsageOutput('hello', expected_output_hello)
        self.assertUsageOutput('hello', expected_output_hello, ['--strict'])

        # Usage for `undef`.
        self.assertUsageOutput('undef', {
            'name': 'undef', 'type': 'system', 'headers': [],
            'libraries': ['undef']
        })
        self.assertUsage('undef', '--strict', returncode=1)

        # Usage from wrong directory.
        self.assertUsageOutput('hello', {
            'name': 'hello', 'type': 'system', 'headers': [],
            'libraries': ['hello']
        }, ['--directory=..'])
        self.assertUsage('hello', '--strict', '--directory=..', returncode=1)
