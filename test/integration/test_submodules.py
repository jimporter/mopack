import json
import os

from . import *


class TestSubmodules(IntegrationTest):
    name = 'submodules'

    def _check_resolve(self, config_file):
        config = os.path.join(test_data_dir, config_file)
        self.assertPopen(['mopack', 'resolve', config])
        self.assertNotExists('mopack/src/hello/hello-multi-bfg/build.bfg')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        for submodules in (['french'], ['english'], ['french', 'english']):
            self.assertPkgConfigLinkage(
                'hello', submodules, pcnames=['hello_' + i for i in submodules]
            )
        self.assertLinkage('hello', returncode=1)

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(bfg9000={}),
            'packages': [
                cfg_directory_pkg(
                    'hello', config,
                    submodules={
                        'names': ['french', 'english'],
                        'required': True,
                    },
                    path={'base': 'cfgdir', 'path': 'hello-multi-bfg'},
                    builders=[cfg_bfg9000_builder()],
                    linkage=cfg_pkg_config_linkage(
                        pcname=None,
                        submodule_map={
                            '*': {'pcname': 'hello_$submodule'},
                        }
                    )
                ),
            ],
        })

    def test_resolve_explicit(self):
        self._check_resolve('mopack-submodules.yml')

    def test_resolve_implicit(self):
        self._check_resolve('mopack-submodules-implicit.yml')


class TestSubmodulesPath(IntegrationTest):
    name = 'submodules-path'

    def test_resolve(self):
        config = os.path.join(test_data_dir, 'mopack-submodules-path.yml')
        self.assertPopen(['mopack', 'resolve', config])
        self.assertNotExists('mopack/src/hello/hello-multi-bfg/build.bfg')
        self.assertExists('mopack/build/hello/')
        self.assertExists('mopack/logs/hello.log')
        self.assertExists('mopack/mopack.json')

        include_path = [os.path.join(test_data_dir, 'hello-multi-bfg',
                                     'include')]
        library_path = [os.path.join(self.pkgbuilddir, 'hello')]
        for submodules in (['french'], ['english'], ['french', 'english']):
            self.assertPathLinkage(
                'hello', submodules, include_path=include_path,
                library_path=library_path,
                libraries=['hello_' + i for i in submodules]
            )
        self.assertLinkage('hello', returncode=1)

        output = json.loads(slurp('mopack/mopack.json'))
        self.assertEqual(output['metadata'], {
            'options': cfg_options(bfg9000={}),
            'packages': [
                cfg_directory_pkg(
                    'hello', config,
                    submodules={
                        'names': ['french', 'english'],
                        'required': True,
                    },
                    path={'base': 'cfgdir', 'path': 'hello-multi-bfg'},
                    builders=[cfg_bfg9000_builder()],
                    linkage=cfg_path_linkage(
                        include_path=[{'base': 'srcdir', 'path': 'include'}],
                        library_path=[{'base': 'builddir', 'path': ''}],
                        submodule_map={'*': {
                            'headers': 'hello_$submodule.hpp',
                            'libraries': 'hello_$submodule',
                        }}
                    )
                ),
            ],
        })
