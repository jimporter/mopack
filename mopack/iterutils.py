from collections.abc import Iterable, Mapping

__all__ = ['isiterable', 'ismapping', 'iterate', 'listify', 'merge_dicts',
           'merge_into_dict']


def isiterable(thing):
    return (isinstance(thing, Iterable) and not isinstance(thing, str) and
            not ismapping(thing))


def ismapping(thing):
    return isinstance(thing, Mapping)


def iterate(thing):
    def generate_none():
        return iter(())

    def generate_one(x):
        yield x

    if thing is None:
        return generate_none()
    elif isiterable(thing):
        return iter(thing)
    else:
        return generate_one(thing)


def listify(thing, always_copy=False, scalar_ok=True, type=list):
    if not always_copy and isinstance(thing, type):
        return thing
    if scalar_ok:
        thing = iterate(thing)
    elif not isiterable(thing):
        raise TypeError('expected an iterable')
    return type(thing)


def merge_into_dict(dst, *args):
    for d in args:
        for k, v in d.items():
            curr = dst.get(k)
            if ismapping(v):
                if curr is None:
                    dst[k] = dict(v)
                elif ismapping(curr):
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
                if curr is not None and isiterable(curr) or ismapping(curr):
                    raise TypeError('type mismatch for {}'.format(k))
                dst[k] = v
            elif k not in dst:
                dst[k] = None  # v is always None here


def merge_dicts(*args):
    dst = {}
    merge_into_dict(dst, *args)
    return dst
