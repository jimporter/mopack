import os
from unittest import mock, skipIf

from . import *


@skipIf('qt' not in test_features, 'skipping test requiring qt')
class TestQt(IntegrationTest):
    name = 'qt'

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-qt.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertExists('mopack/mopack.json')

        if platform_name() == 'windows':
            self.assertPathUsage('Qt5', ['Widgets'], type='system',
                                 include_path=mock.ANY,
                                 library_path=mock.ANY,
                                 libraries=['Qt5Widgets', 'Qt5Core'],
                                 version='')
        else:
            self.assertPkgConfigUsage('Qt5', ['Widgets'], type='system',
                                      pcnames=['Qt5Widgets'],
                                      pkg_config_path=[])

        self.assertUsage('Qt5', returncode=1)

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(),
            'packages': [
                cfg_system_pkg(
                    'Qt5', config,
                    submodules={'names': '*', 'required': True},
                    usage=cfg_system_usage(
                        pcname='Qt5',
                        auto_link=False,
                        explicit_version=None,
                        include_path=mock.ANY,
                        library_path=mock.ANY,
                        headers=[],
                        submodule_map=mock.ANY,
                    )
                ),
            ],
        })
