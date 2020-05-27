import os
from contextlib import contextmanager


def try_join(a, b):
    if os.path.isabs(b):
        return os.path.normpath(b)
    return os.path.abspath(os.path.join(a, b))


@contextmanager
def pushd(dirname, makedirs=False, mode=0o777, exist_ok=False):
    old = os.getcwd()
    if makedirs:
        os.makedirs(dirname, mode, exist_ok)

    os.chdir(dirname)
    yield
    os.chdir(old)
