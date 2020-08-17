import os
import subprocess
import tempfile
import unittest

from .. import *

# Also supported: 'apt'
test_features = {'boost'}
for i in os.getenv('MOPACK_EXTRA_TESTS', '').split(' '):
    if i:
        test_features.add(i)
for i in os.getenv('MOPACK_SKIPPED_TESTS', '').split(' '):
    if i:
        test_features.remove(i)


def stage_dir(name, chdir=True):
    stage = tempfile.mkdtemp(prefix=name + '-', dir=test_stage_dir)
    if chdir:
        os.chdir(stage)
    return stage


def slurp(filename):
    with open(filename) as f:
        return f.read()


class SubprocessError(unittest.TestCase.failureException):
    def __init__(self, message):
        unittest.TestCase.failureException.__init__(
            self, '\n{line}\n{msg}\n{line}'.format(line='-' * 60, msg=message)
        )


class IntegrationTest(unittest.TestCase):
    def assertExists(self, path):
        if not os.path.exists(path):
            raise unittest.TestCase.failureException(
                '{!r} does not exist'.format(os.path.normpath(path))
            )

    def assertNotExists(self, path):
        if os.path.exists(path):
            raise unittest.TestCase.failureException(
                '{!r} exists'.format(os.path.normpath(path))
            )

    def assertPopen(self, command, returncode=0):
        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        output = proc.communicate()[0]
        if proc.returncode != returncode:
            raise SubprocessError(output)
        return output

    def assertOutput(test, command, output, *args, **kwargs):
        test.assertEqual(assertPopen(command, *args, **kwargs), output)
