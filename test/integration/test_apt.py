import json
import os
from unittest import mock, skipIf

from . import *


@skipIf('apt' not in test_features,
        'skipping apt tests; add `apt` to `MOPACK_EXTRA_TESTS` to enable')
class TestApt(IntegrationTest):
    name = 'apt'

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-apt.yml')
        self.assertPopen(mopack_cmd('resolve', config),
                         extra_env={'PKG_CONFIG': 'nonexist'})
        self.assertExists('mopack/logs/apt.log')
        self.assertExists('mopack/mopack.json')

        self.assertPathLinkage('ogg', type='system', version=mock.ANY)
        self.assertPathLinkage('zlib', type='system', version=mock.ANY,
                               libraries=['z'])

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(),
            'packages': [
                cfg_apt_pkg(
                    'ogg', config,
                    remote=['libogg-dev'],
                    linkage=cfg_system_linkage(
                        pcname='ogg',
                        libraries=['ogg']
                    )
                ),
                cfg_apt_pkg(
                    'zlib', config,
                    remote=['zlib1g-dev'],
                    linkage=cfg_system_linkage(
                        pcname='zlib',
                        libraries=['z']
                    )
                ),
            ],
        })

        self.assertPopen(mopack_cmd('deploy'))
