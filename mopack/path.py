import errno
import os
from contextlib import contextmanager


def makedirs(path, mode=0o777, exist_ok=False):
    try:
        os.makedirs(path, mode)
    except OSError as e:
        if not exist_ok or e.errno != errno.EEXIST or not os.path.isdir(path):
            raise


# Make an alias since the function below masks the module-level function with
# one of its parameters.
_makedirs = makedirs


@contextmanager
def pushd(dirname, makedirs=False, mode=0o777, exist_ok=False):
    old = os.getcwd()
    if makedirs:
        _makedirs(dirname, mode, exist_ok)

    os.chdir(dirname)
    yield
    os.chdir(old)
