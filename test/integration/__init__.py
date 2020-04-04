import os
import subprocess
import tempfile
import unittest

from .. import *


class SubprocessError(unittest.TestCase.failureException):
    def __init__(self, message):
        unittest.TestCase.failureException.__init__(
            self, '\n{line}\n{msg}\n{line}'.format(line='-' * 60, msg=message)
        )


def assertPopen(command, returncode=0):
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


def stage_dir(name):
    stage = tempfile.mkdtemp(prefix=name + '-', dir=test_stage_dir)
    os.chdir(stage)
    return stage
