import os
import subprocess
import tempfile
import unittest

from .. import *

from mopack.iterutils import listify


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
    def __init__(self, returncode, env, message):
        envstr = ''.join('  {} = {}\n'.format(k, v)
                         for k, v in (env or {}).items())
        msg = 'returned {returncode}\n{env}{line}\n{msg}\n{line}'.format(
            returncode=returncode, env=envstr, line='-' * 60, msg=message
        )
        super().__init__(msg)


class IntegrationTest(unittest.TestCase):
    def assertExistence(self, path, exists):
        if os.path.exists(path) != exists:
            msg = '{!r} does not exist' if exists else '{!r} exists'
            raise unittest.TestCase.failureException(
                msg.format(os.path.normpath(path))
            )

    def assertExists(self, path):
        self.assertExistence(path, True)

    def assertNotExists(self, path):
        self.assertExistence(path, False)

    def assertPopen(self, command, *, env=None, extra_env=None, returncode=0):
        final_env = env if env is not None else os.environ
        if extra_env:
            final_env = final_env.copy()
            final_env.update(extra_env)

        proc = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            env=final_env, universal_newlines=True
        )
        if not (returncode == 'any' or
                (returncode == 'fail' and proc.returncode != 0) or
                proc.returncode in listify(returncode)):
            raise SubprocessError(proc.return_code, extra_env or env,
                                  proc.stdout)
        return proc.stdout

    def assertOutput(self, command, output, *args, **kwargs):
        self.assertEqual(self.assertPopen(command, *args, **kwargs), output)
