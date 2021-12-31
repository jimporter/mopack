import os
from unittest import skipIf

from . import *


@skipIf('qt' not in test_features, 'skipping test requiring qt')
class TestQt(IntegrationTest):
    name = 'qt'
    maxDiff = None

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-qt.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertExists('mopack/mopack.json')

        if platform_name() == 'windows':
            self.assertPathUsage('Qt5', ['Widgets'], type='system',
                                 include_path=AlwaysEqual(),
                                 library_path=AlwaysEqual(),
                                 libraries=['Qt5Widgets', 'Qt5Core'],
                                 version='')
        else:
            self.assertPkgConfigUsage('Qt5', ['Widgets'], type='system',
                                      path=[], pcfiles=['Qt5Widgets'])

        self.assertUsage('Qt5', returncode=1)

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(),
            'packages': [
                cfg_system_pkg(
                    'Qt5', config,
                    submodules={'names': '*', 'required': True},
                    usage=cfg_system_usage(
                        pcfile='Qt5',
                        auto_link=False,
                        explicit_version=None,
                        include_path=AlwaysEqual(),
                        library_path=AlwaysEqual(),
                        headers=[],
                        submodule_map=AlwaysEqual(),
                    )
                ),
            ],
        })
