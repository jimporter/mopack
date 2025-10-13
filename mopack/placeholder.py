import re

from . import iterutils
from .freezedried import auto_dehydrate

_known_placeholders = []


def placeholder_type(cls):
    _known_placeholders.append(cls)
    return cls


class PlaceholderValue:
    def __init__(self, value):
        self.value = value

    def __eq__(self, rhs):
        if not isinstance(rhs, PlaceholderValue):
            return NotImplemented
        return self.value == rhs.value

    def dehydrate(self):
        return auto_dehydrate(self.value)

    @classmethod
    def rehydrate(cls, config, **kwargs):
        for cls in _known_placeholders:
            try:
                return PlaceholderValue(cls.rehydrate(config, **kwargs))
            except TypeError:
                continue
        raise TypeError('unrecognized placeholder')

    def __str__(self):
        raise NotImplementedError('{} cannot be converted to str'
                                  .format(type(self).__name__))

    def __repr__(self):
        return '@{!r}'.format(self.value)


class PlaceholderString:
    def __init__(self, *args):
        self.__bits = tuple(self.__canonicalize(args))

    @staticmethod
    def __canonicalize(value):
        def flatten_bits(value):
            for i in value:
                if isinstance(i, PlaceholderString):
                    yield from i.__bits
                elif isinstance(i, (str, PlaceholderValue)):
                    yield i
                else:  # pragma: no cover
                    raise TypeError(type(i))

        bits = flatten_bits(value)
        try:
            last = next(bits)
        except StopIteration:
            return

        for i in bits:
            if isinstance(last, str) and isinstance(i, str):
                last += i
            else:
                yield last
                last = i
        yield last

    @classmethod
    def make(cls, *args, simplify=False):
        result = PlaceholderString(*args)
        if simplify:
            return result.simplify()
        return result

    def dehydrate(self):
        return [auto_dehydrate(i) for i in self.__bits]

    @classmethod
    def rehydrate(cls, config, **kwargs):
        def rehydrate_each(value, **kwargs):
            if isinstance(value, str):
                return value
            return PlaceholderValue.rehydrate(value, **kwargs)

        return PlaceholderString(*[
            rehydrate_each(i, **kwargs) for i in config
        ])

    @property
    def bits(self):
        return self.__bits

    def simplify(self, *, unbox=False):
        if len(self.__bits) == 0:
            return ''
        elif len(self.__bits) == 1:
            if isinstance(self.__bits[0], PlaceholderValue):
                if unbox:
                    return self.__bits[0].value
            else:
                return self.__bits[0]
        return self

    def unbox(self, simplify=False):
        if simplify:
            simplified = self.simplify(unbox=True)
            if simplified is not self:
                return simplified
        return tuple(i.value if isinstance(i, PlaceholderValue) else i
                     for i in self.__bits)

    def replace(self, placeholder, value, *, simplify=False):
        def each(i):
            if isinstance(i, PlaceholderValue) and i.value == placeholder:
                return value
            return i
        return self.make(*[each(i) for i in self.__bits], simplify=simplify)

    def stash(self):
        stashed = ''
        placeholders = []
        for i in self.__bits:
            if isinstance(i, PlaceholderValue):
                stashed += '\x11{}\x13'.format(len(placeholders))
                placeholders.append(i)
            else:
                stashed += i.replace('\x11', '\x11\x13')
        return stashed, placeholders

    @classmethod
    def unstash(cls, string, placeholders):
        bits = []
        last = 0
        for m in re.finditer('\x11([^\x11]*)\x13', string):
            if m.start() > last:
                bits.append(string[last:m.start()])
            if len(m.group(1)):
                bits.append(placeholders[int(m.group(1))])
            else:
                bits.append('\x11')
            last = m.end()
        if last < len(string):
            bits.append(string[last:])

        return PlaceholderString(*bits)

    def __add__(self, rhs):
        return PlaceholderString(self, rhs)

    def __radd__(self, lhs):
        return PlaceholderString(lhs, self)

    def __eq__(self, rhs):
        if not isinstance(rhs, PlaceholderString):
            return NotImplemented
        return self.__bits == rhs.__bits

    def __str__(self):
        raise NotImplementedError('{} cannot be converted to str'
                                  .format(type(self).__name__))

    def __repr__(self):
        return '|{}|'.format(', '.join(repr(i) for i in self.__bits))


def placeholder(value):
    return PlaceholderString(PlaceholderValue(value))


def map_placeholder(value, fn):
    if iterutils.issequence(value):
        return [map_placeholder(i, fn) for i in value]
    elif iterutils.ismapping(value):
        return {k: map_placeholder(v, fn) for k, v in value.items()}
    elif isinstance(value, PlaceholderString):
        return fn(value)
    else:
        return value
