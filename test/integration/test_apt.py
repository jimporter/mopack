import json
import os
from unittest import skipIf

from . import *


@skipIf('apt' not in test_features,
        'skipping apt tests; add `apt` to `MOPACK_EXTRA_TESTS` to enable')
class TestApt(IntegrationTest):
    name = 'apt'

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-apt.yml')
        self.assertPopen(['mopack', 'resolve', config],
                         extra_env={'PKG_CONFIG': 'nonexist'})
        self.assertExists('mopack/logs/apt.log')
        self.assertExists('mopack/mopack.json')

        self.assertPathUsage('ogg', type='system', version=AlwaysEqual())
        self.assertPathUsage('zlib', type='system', version=AlwaysEqual(),
                             libraries=['z'])

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(),
            'packages': [
                cfg_apt_pkg(
                    'ogg', config,
                    remote=['libogg-dev'],
                    usage=cfg_system_usage(
                        pcname='ogg',
                        libraries=['ogg']
                    )
                ),
                cfg_apt_pkg(
                    'zlib', config,
                    remote=['zlib1g-dev'],
                    usage=cfg_system_usage(
                        pcname='zlib',
                        libraries=['z']
                    )
                ),
            ],
        })

        self.assertPopen(['mopack', 'deploy'])
