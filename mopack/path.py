import os
from contextlib import contextmanager
from enum import Enum

from .freezedried import FreezeDried

__all__ = ['Path', 'pushd']


@contextmanager
def pushd(dirname, makedirs=False, mode=0o777, exist_ok=False):
    old = os.getcwd()
    if makedirs:
        os.makedirs(dirname, mode, exist_ok)

    os.chdir(dirname)
    try:
        yield
    finally:
        os.chdir(old)


class Path(FreezeDried):
    class Base(Enum):
        absolute = 0
        cfgdir = 1
        srcdir = 2
        builddir = 3

        @classmethod
        def ensure_base(cls, base):
            if isinstance(base, cls):
                return base
            try:
                return cls[base]
            except KeyError:
                raise TypeError('{!r} is not a valid base'.format(base))

        @classmethod
        def filter(cls, bases, filter_bases):
            bases = (cls.ensure_base(i) for i in bases)
            filter_bases = {cls.ensure_base(i) for i in filter_bases}
            return [i for i in bases if i in filter_bases]

    def __init__(self, base, path):
        if not isinstance(path, str):
            raise TypeError('expected a string')
        self.path = os.path.normpath(path)
        if self.path == os.path.curdir:
            self.path = ''
        base = self.Base.ensure_base(base)

        if os.path.isabs(self.path):
            self.base = self.Base.absolute
        elif base == self.Base.absolute:
            raise ValueError('base is absolute, but path is relative')
        elif ( hasattr(os.path, 'splitdrive') and
               os.path.splitdrive(self.path)[0] ):
            raise ValueError('relative paths with drives not supported')
        else:
            self.base = base

    def dehydrate(self):
        return [self.base.name, self.path]

    @classmethod
    def rehydrate(cls, config, **kwargs):
        if not isinstance(config, list) or len(config) != 2:
            raise TypeError('expected a list')
        return cls(cls.Base[config[0]], config[1])

    @classmethod
    def ensure_path(cls, path, bases):
        if len(bases) == 0:
            raise TypeError('no bases specified')
        bases = [cls.Base.ensure_base(i) for i in bases]
        if isinstance(path, Path):
            if path.base not in bases:
                raise TypeError('invalid base {!r}'.format(path.base.name))
            return path
        return cls(bases[0], path)

    def is_abs(self):
        return self.base == self.Base.absolute

    def is_inner(self):
        return (self.path != os.path.pardir and
                not self.path.startswith(os.path.pardir + os.path.sep))

    def __add__(self, rhs):
        if not isinstance(rhs, str):
            return NotImplemented

        if not self.path:
            suffix = os.path.normpath(rhs)
            if suffix and suffix[0] != os.path.sep:
                raise ValueError('expected a directory separator')
            return Path(self.base, suffix[1:])
        return Path(self.base, self.path + rhs)

    def __eq__(self, rhs):
        if not isinstance(rhs, Path):
            return NotImplemented
        return self.base == rhs.base and self.path == rhs.path

    def string(self, **kwargs):
        if self.base == self.Base.absolute:
            return os.path.abspath(self.path)
        base = kwargs[self.base.name]
        path = os.path.join(base, self.path) if self.path else base
        return os.path.abspath(path)

    def __str__(self):
        raise NotImplementedError('{} cannot be converted to str'
                                  .format(type(self).__name__))

    def __repr__(self):
        if self.base == self.Base.absolute:
            path = self.path
        else:
            path = '$({})/{})'.format(self.base.name, self.path)
        return "<{}({!r})>".format(type(self).__name__, path)
