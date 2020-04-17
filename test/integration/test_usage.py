import json
import os
import yaml

from mopack.path import pushd

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

        # Usage for `foo`.
        expected_output_foo = {
            'name': 'foo',
            'type': 'pkg-config',
            'path': os.path.join(self.stage, 'mopack', 'build', 'foo',
                                 'pkgconfig'),
        }
        self.assertUsageOutput('foo', expected_output_foo)
        self.assertUsageOutput('foo', expected_output_foo, ['--strict'])

        # Usage for `undef`.
        self.assertUsageOutput('undef', {'name': 'undef', 'type': 'system'})
        self.assertUsage('undef', '--strict', returncode=1)

        # Usage from wrong directory.
        self.assertUsageOutput('foo', {'name': 'foo', 'type': 'system'},
                               ['--directory=..'])
        self.assertUsage('foo', '--strict', '--directory=..', returncode=1)
