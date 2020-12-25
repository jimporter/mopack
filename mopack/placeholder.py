import re


class PlaceholderValue:
    def __init__(self, value):
        self.value = value

    def __eq__(self, rhs):
        if not isinstance(rhs, PlaceholderValue):
            return NotImplemented
        return self.value == rhs.value

    def __str__(self):
        raise NotImplementedError('{} cannot be converted to str'
                                  .format(type(self).__name__))

    def __repr__(self):
        return '@({!r})'.format(self.value)


class PlaceholderString:
    def __init__(self, *args):
        self.__bits = tuple(self.__canonicalize(args))

    @staticmethod
    def __canonicalize(value):
        def flatten_bits(value):
            for i in value:
                if isinstance(i, PlaceholderString):
                    yield from i.bits
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
            if len(result.bits) == 0:
                return ''
            elif len(result.bits) == 1 and isinstance(result.bits[0], str):
                return result.bits[0]
        return result

    @property
    def bits(self):
        return self.__bits

    def unbox(self, simplify=False):
        if simplify:
            if len(self.bits) == 0:
                return ''
            elif len(self.bits) == 1:
                if isinstance(self.bits[0], PlaceholderValue):
                    return self.bits[0].value
                return self.bits[0]
        return tuple(i.value if isinstance(i, PlaceholderValue) else i
                     for i in self.__bits)

    def replace(self, placeholder, value, *, simplify=False):
        def each(i):
            if isinstance(i, PlaceholderValue) and i.value == placeholder:
                return value
            return i
        return self.make(*[each(i) for i in self.bits], simplify=simplify)

    def stash(self):
        stashed = ''
        placeholders = []
        for i in self.bits:
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
        return '|{}|'.format(', '.join(repr(i) for i in self.bits))


def placeholder(value):
    return PlaceholderString(PlaceholderValue(value))


def map_recursive(value, fn):
    if isinstance(value, list):
        return [map_recursive(i, fn) for i in value]
    elif isinstance(value, dict):
        return {k: map_recursive(v, fn) for k, v in value.items()}
    elif isinstance(value, PlaceholderString):
        return fn(value)
    else:
        return value


class PlaceholderFD:
    def __init__(self, *args):
        self._placeholders = args

    def _dehydrate_placeholder(self, value):
        if isinstance(value, PlaceholderValue):
            for i, ph in enumerate(self._placeholders):
                if value.value == ph:
                    return i
            raise ValueError('unrecognized placeholder {!r}'.format(value))
        return value

    def _rehydrate_placeholder(self, value):
        if isinstance(value, int):
            return PlaceholderValue(self._placeholders[value])
        return value

    def dehydrate(self, value):
        return map_recursive(value, lambda value: {'#phs#': [
            self._dehydrate_placeholder(i) for i in value.bits
        ]})

    def rehydrate(self, value, **kwargs):
        if isinstance(value, dict):
            if list(value.keys()) == ['#phs#']:
                return PlaceholderString(*[self._rehydrate_placeholder(i)
                                           for i in value['#phs#']])
            return {k: self.rehydrate(v, **kwargs) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.rehydrate(i, **kwargs) for i in value]
        else:
            return value
