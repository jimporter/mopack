import os
from unittest import TestCase

from . import *


class TestSdist(TestCase):
    def setUp(self):
        self.stage = stage_dir('sdist')

    def assertExists(self, path):
        if not os.path.exists(path):
            raise unittest.TestCase.failureException(
                "'{}' does not exist".format(path)
            )

    def test_fetch(self):
        config = os.path.join(test_data_dir, 'mopack-tarball.yml')
        assertPopen(['mopack', 'fetch', config])
        self.assertExists('mopack/bfg_project/build.bfg')
        self.assertExists('mopack/bfg_project/build/')
        self.assertExists('mopack/foo.log')
        self.assertExists('mopack/mopack.json')
