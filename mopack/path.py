import fnmatch
import os
import posixpath
import re
from contextlib import contextmanager

from .iterutils import iterate

__all__ = ['filter_glob', 'Glob', 'pushd', 'try_join']


def try_join(a, b):
    if os.path.isabs(b):
        return os.path.abspath(b)
    return os.path.abspath(os.path.join(a, b))


@contextmanager
def pushd(dirname, makedirs=False, mode=0o777, exist_ok=False):
    old = os.getcwd()
    if makedirs:
        os.makedirs(dirname, mode, exist_ok)

    os.chdir(dirname)
    yield
    os.chdir(old)


class Glob:
    _glob_ex = re.compile('([*?[])')
    _starstar = object()

    def __init__(self, pattern):
        if pattern == '':
            self._directory = False
            self._bits = []
        else:
            bits = pattern.split(posixpath.sep)
            self._directory = bits[-1] == ''
            if self._directory:
                del bits[-1]

            self._bits = list(self._translate_bits(bits))

    @classmethod
    def _translate_bits(cls, bits):
        starstar = False
        if bits[0] != '':
            starstar = True
            yield cls._starstar

        for i in bits:
            if i == '**':
                # This line is fully-covered, but coverage.py can't detect it
                # correctly...
                if not starstar:  # pragma: no branch
                    starstar = True
                    yield cls._starstar
                continue

            starstar = False
            if cls._glob_ex.search(i):
                yield re.compile(fnmatch.translate(i)).match
            elif i:
                yield cls._match_string(i)

    @staticmethod
    def _match_string(s):
        return lambda x: x == s

    def match(self, path, *, match_parent=True, match_child=True):
        path_bits = path.split(posixpath.sep)
        is_directory = path_bits[-1] == ''
        if is_directory:
            del path_bits[-1]

        path_iter = iter(path_bits)
        recursing = False
        for i in self._bits:
            if i is self._starstar:
                recursing = True
                continue

            if recursing:
                p = None
                for p in path_iter:
                    if i(p):
                        break
                else:
                    if p is None:
                        # `path` is a parent of our pattern.
                        return bool(is_directory and match_parent)
                    return False
                recursing = False
                continue

            p = next(path_iter, None)
            if p is None:
                # `path` is a parent of our pattern.
                return bool(is_directory and match_parent)
            if not i(p):
                return False

        if next(path_iter, None) is not None:
            # `path` is a child of our pattern.
            return bool(match_child) or recursing
        return is_directory if (self._directory or recursing) else True


def filter_glob(patterns, paths, **kwargs):
    globs = [i if isinstance(i, Glob) else Glob(i) for i in iterate(patterns)]
    for p in paths:
        for g in globs:
            if g.match(p, **kwargs):
                yield p
                break
