import json
import os

from mopack.platforms import platform_name

from . import *


class TestConditional(IntegrationTest):
    name = 'conditional'

    def test_resolve(self):
        want_tarball = platform_name() == 'windows'

        config = os.path.join(test_data_dir, 'mopack-conditional.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertExistence('mopack/src/hello/hello-bfg/build.bfg',
                             want_tarball)
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        self.assertPkgConfigUsage('hello')

        output = json.loads(slurp('mopack/mopack.json'))
        if want_tarball:
            hellopkg = cfg_tarball_pkg(
                'hello', config,
                path={'base': 'cfgdir', 'path': 'hello-bfg.tar.gz'},
                guessed_srcdir='hello-bfg',
                builder=cfg_bfg9000_builder('hello'),
                usage=cfg_pkg_config_usage(pcfile='hello')
            )
        else:
            hellopkg = cfg_directory_pkg(
                'hello', config,
                path={'base': 'cfgdir', 'path': 'hello-bfg'},
                builder=cfg_bfg9000_builder('hello'),
                usage=cfg_pkg_config_usage(pcfile='hello')
            )
        self.assertEqual(output['metadata'], {
            'options': cfg_options(bfg9000={}),
            'packages': [hellopkg],
        })
