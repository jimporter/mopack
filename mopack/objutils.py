import functools
from .iterutils import isiterable, ismapping

__all__ = ['hashify', 'memoize', 'memoize_method', 'Unset']


class _UnsetType:
    def __bool__(self):
        return False

    def __eq__(self, rhs):
        return isinstance(rhs, _UnsetType) or rhs is None

    def dehydrate(self):
        return None

    @classmethod
    def rehydrate(self, value, **kwargs):
        if value is not None:
            raise ValueError('expected None')
        return Unset

    def __repr__(self):
        return '<Unset>'


Unset = _UnsetType()


def hashify(thing):
    if ismapping(thing):
        return tuple((hashify(k), hashify(v)) for k, v in thing.items())
    elif isiterable(thing):
        return tuple(hashify(i) for i in thing)
    return thing


def memoize(fn):
    cache = {}

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        key = (hashify(args), hashify(kwargs))
        if key in cache:
            return cache[key]
        result = cache[key] = fn(*args, **kwargs)
        return result

    def reset():
        cache.clear()

    wrapper._reset = reset
    return wrapper


def memoize_method(fn):
    cachename = '_memoize_cache_{}'.format(fn.__name__)

    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        try:
            cache = getattr(self, cachename)
        except AttributeError:
            cache = {}
            setattr(self, cachename, cache)

        key = (hashify(args), hashify(kwargs))
        if key in cache:
            return cache[key]
        result = cache[key] = fn(self, *args, **kwargs)
        return result

    def reset(self):
        try:
            getattr(self, cachename).clear()
        except AttributeError:
            pass

    wrapper._reset = reset
    return wrapper
