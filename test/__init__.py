import os
import shutil
import subprocess

from mopack.shell import split_posix_str


__all__ = ['AlwaysEqual', 'call_pkg_config', 'this_dir', 'test_data_dir',
           'test_stage_dir']

this_dir = os.path.abspath(os.path.dirname(__file__))
test_data_dir = os.path.join(this_dir, 'data')
test_stage_dir = os.path.join(this_dir, 'stage')

# Clear the stage directory for this test run.
if os.path.exists(test_stage_dir):
    shutil.rmtree(test_stage_dir)
os.makedirs(test_stage_dir)


class AlwaysEqual:
    def __eq__(self, rhs):
        return True


def call_pkg_config(package, options, path=None):
    extra_kwargs = {}
    if path:
        env = os.environ.copy()
        env['PKG_CONFIG_PATH'] = path
        extra_kwargs['env'] = env

    return split_posix_str(subprocess.run(
        [os.environ.get('PKG_CONFIG', 'pkg-config'), package] + options,
        check=True, universal_newlines=True, stdout=subprocess.PIPE,
        **extra_kwargs
    ).stdout.strip(), escapes=True)
