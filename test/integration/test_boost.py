import os
from unittest import mock, skipIf

from . import *


@skipIf('boost' not in test_features, 'skipping test requiring boost')
class TestBoost(IntegrationTest):
    name = 'boost'

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-boost.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertExists('mopack/mopack.json')

        self.assertPathLinkage('boost', type='system',
                               auto_link=platform_name() == 'windows',
                               include_path=mock.ANY,
                               library_path=mock.ANY,
                               libraries=[],
                               version=mock.ANY)

        pkgconfdir = os.path.join(self.stage, 'mopack', 'pkgconfig')
        version = call_pkg_config(['boost'], ['--modversion'], path=pkgconfdir,
                                  split=False)

        self.assertPathLinkage(
            'boost', ['regex'], type='system',
            auto_link=platform_name() == 'windows',
            pcnames=(['boost'] if platform_name() == 'windows'
                     else ['boost[regex]']),
            include_path=mock.ANY,
            library_path=mock.ANY,
            libraries=([] if platform_name() == 'windows'
                       else ['boost_regex']),
            version=version
        )

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(),
            'packages': [
                cfg_system_pkg(
                    'boost', config,
                    submodules={'names': '*', 'required': False},
                    linkage=cfg_system_linkage(
                        pcname='boost',
                        auto_link=platform_name() == 'windows',
                        explicit_version={
                            'type': 'regex',
                            'file': 'boost/version.hpp',
                            'regex': [
                                (r'^#\s*define\s+BOOST_LIB_VERSION\s+' +
                                 r'"([\d_]+)"'),
                                ['_', '.'],
                            ],
                        },
                        include_path=mock.ANY,
                        library_path=mock.ANY,
                        headers=['boost/version.hpp'],
                        submodule_map=mock.ANY,
                    )
                ),
            ],
        })
