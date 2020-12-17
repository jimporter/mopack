import json
import os
from unittest import skipIf

from mopack.platforms import platform_name

from . import *


@skipIf('apt' not in test_features,
        'skipping apt tests; add `apt` to `MOPACK_EXTRA_TESTS` to enable')
class TestApt(IntegrationTest):
    name = 'apt'

    def _usage(self, name, headers=[], libraries=[]):
        return {
            'type': 'system',
            'pcfile': name,
            'auto_link': False,
            'include_path': [],
            'library_path': [],
            'headers': headers,
            'libraries': libraries,
            'compile_flags': [],
            'link_flags': [],
        }

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-apt.yml')
        self.assertPopen(['mopack', 'resolve', config],
                         extra_env={'PKG_CONFIG': 'nonexist'})
        self.assertExists('mopack/logs/apt.log')
        self.assertExists('mopack/mopack.json')

        self.assertPathUsage('ogg')
        self.assertPathUsage('zlib', libraries=['z'])

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': {
                'common': {
                    'target_platform': platform_name(),
                    'env': AlwaysEqual(),
                    'deploy_paths': {},
                },
                'builders': [],
                'sources': [],
            },
            'packages': [{
                'name': 'ogg',
                'config_file': config,
                'resolved': True,
                'source': 'apt',
                'submodules': None,
                'should_deploy': True,
                'remote': 'libogg-dev',
                'repository': None,
                'usage': self._usage('ogg', libraries=[
                    {'name': 'ogg', 'type': 'guess'},
                ]),
            }, {
                'name': 'zlib',
                'config_file': config,
                'source': 'apt',
                'resolved': True,
                'submodules': None,
                'should_deploy': True,
                'remote': 'zlib1g-dev',
                'repository': None,
                'usage': self._usage('zlib', libraries=[
                    {'name': 'zlib', 'type': 'guess'},
                ]),
            }],
        })
