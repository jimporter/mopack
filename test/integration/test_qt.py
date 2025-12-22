import os
from unittest import mock, skipIf

from . import *


@skipIf('qt' not in test_features, 'skipping test requiring qt')
class TestQt(IntegrationTest):
    name = 'qt'

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-qt.yml')
        self.assertPopen(mopack_cmd('resolve', config))
        self.assertExists('mopack/mopack.json')

        if platform_name() == 'windows':
            self.assertPathLinkage(
                'Qt5', ['Widgets'], type='system', version='',
                include_path=mock.ANY, library_path=mock.ANY,
                libraries=['Qt5Widgets', 'Qt5Core']
            )
        else:
            if platform_name() == 'darwin':
                # Qt on macOS uses frameworks, not libraries.
                libraries = mock.ANY
            else:
                libraries = ['Qt5Widgets', 'Qt5Gui', 'Qt5Core']
            self.assertPkgConfigLinkage(
                'Qt5', ['Widgets'], type='system', pcnames=['Qt5Widgets'],
                pkg_config_path=[], version=mock.ANY, include_path=mock.ANY,
                compile_flags=mock.ANY, library_path=mock.ANY,
                libraries=libraries, link_flags=mock.ANY
            )

        self.assertLinkage('Qt5', returncode=1)

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(),
            'packages': [
                cfg_system_pkg(
                    'Qt5', config,
                    submodules='*',
                    submodule_required=True,
                    linkage=cfg_system_linkage(
                        pcname='Qt5',
                        auto_link=False,
                        explicit_version=None,
                        include_path=mock.ANY,
                        library_path=mock.ANY,
                        headers=[],
                        submodule_linkage=mock.ANY,
                    )
                ),
            ],
        })
