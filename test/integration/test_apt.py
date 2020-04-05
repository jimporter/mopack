import os
from unittest import skipIf, TestCase

from . import *


@skipIf(os.getenv('MOPACK_TEST_APT') not in ['1', 'true'],
        'skipping apt tests; set MOPACK_TEST_APT=1 to enable')
class TestApt(TestCase):
    def setUp(self):
        self.stage = stage_dir('apt')

    def assertExists(self, path):
        if not os.path.exists(path):
            raise unittest.TestCase.failureException(
                "'{}' does not exist".format(path)
            )

    def test_fetch(self):
        config = os.path.join(test_data_dir, 'mopack-apt.yml')
        assertPopen(['mopack', 'fetch', config])
        self.assertExists('mopack/apt.log')
        self.assertExists('mopack/mopack.json')
