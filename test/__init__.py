import os
import shutil
import subprocess
from subprocess import run as subprocess_run

from mopack.iterutils import listify
from mopack.shell import split_posix_str


__all__ = ['call_pkg_config', 'test_dir', 'test_data_dir', 'test_stage_dir']

test_dir = os.path.abspath(os.path.dirname(__file__))
test_data_dir = os.path.join(test_dir, 'data')
test_stage_dir = os.path.join(test_dir, 'stage')

# Clear the stage directory for this test run.
if os.path.exists(test_stage_dir):
    shutil.rmtree(test_stage_dir)
os.makedirs(test_stage_dir)


def call_pkg_config(package, options, *, path=None, split=True):
    extra_kwargs = {}
    if path:
        env = os.environ.copy()
        env['PKG_CONFIG_PATH'] = path
        extra_kwargs['env'] = env

    pkg_config = os.environ.get('PKG_CONFIG', 'pkg-config')
    # Use subprocess_run to ensure that we get the real function, not a mock.
    output = subprocess_run(
        [pkg_config] + listify(package) + options,
        check=True, universal_newlines=True, stdout=subprocess.PIPE,
        **extra_kwargs
    ).stdout.strip()

    if split:
        return split_posix_str(output, escapes=True)
    else:
        return output
