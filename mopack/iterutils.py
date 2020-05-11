from collections import Iterable

__all__ = ['isiterable', 'merge_dicts', 'merge_into_dict']


def isiterable(thing):
    return isinstance(thing, Iterable) and not isinstance(thing, str)


def merge_into_dict(dst, *args):
    for d in args:
        for k, v in d.items():
            curr = dst.get(k)
            if isinstance(v, dict):
                if curr is None:
                    dst[k] = dict(v)
                elif isinstance(curr, dict):
                    merge_into_dict(curr, v)
                else:
                    raise TypeError('type mismatch for {}'.format(k))
            elif isiterable(v):
                if curr is None:
                    dst[k] = type(v)(v)
                elif isiterable(curr):
                    curr.extend(v)
                else:
                    raise TypeError('type mismatch for {}'.format(k))
            elif v is not None:
                if curr is not None and isiterable(curr):
                    raise TypeError('type mismatch for {}'.format(k))
                dst[k] = v
            elif k not in dst:
                dst[k] = None  # v is always None here


def merge_dicts(*args):
    dst = {}
    merge_into_dict(dst, *args)
    return dst
