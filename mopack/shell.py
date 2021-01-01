from collections.abc import MutableSequence
from enum import Enum
from shlex import shlex

from .freezedried import auto_dehydrate
from .iterutils import isiterable
from .path import Path
from .placeholder import PlaceholderString
from .platforms import platform_name


_Token = Enum('Token', ['char', 'quote', 'space'])
_State = Enum('State', ['between', 'char', 'word', 'quoted'])


def split_posix_str(s, type=list, escapes=False):
    if not isinstance(s, str):
        raise TypeError('expected a string')
    lexer = shlex(s, posix=True)
    lexer.commenters = ''
    if not escapes:
        lexer.escape = ''
    lexer.whitespace_split = True
    return type(lexer)


def _tokenize_windows(s):
    escapes = 0
    for c in s:
        if c == '\\':
            escapes += 1
        elif c == '"':
            for i in range(escapes // 2):
                yield (_Token.char, type(s)('\\'))
            yield (_Token.char, '"') if escapes % 2 else (_Token.quote, None)
            escapes = 0
        else:
            for i in range(escapes):
                yield (_Token.char, type(s)('\\'))
            yield ((_Token.space if c in ' \t' else _Token.char), c)
            escapes = 0


def split_windows_str(s, type=list):
    if not isinstance(s, str):
        raise TypeError('expected a string')

    mutable = isinstance(type, MutableSequence)
    state = _State.between
    args = (type if mutable else list)()

    for tok, value in _tokenize_windows(s):
        if state == _State.between:
            if tok == _Token.char:
                args.append(value)
                state = _State.word
            elif tok == _Token.quote:
                args.append('')
                state = _State.quoted
        elif state == _State.word:
            if tok == _Token.quote:
                state = _State.quoted
            elif tok == _Token.char:
                args[-1] += value
            else:  # tok == _Token.space
                state = _State.between
        else:  # state == _State.quoted
            if tok == _Token.quote:
                state = _State.word
            else:
                args[-1] += value

    return args if mutable else type(args)


def split_native_str(s, type=list):
    if platform_name() == 'windows':
        return split_windows_str(s, type)
    return split_posix_str(s, type)


class ShellArguments(MutableSequence):
    def __init__(self, args=[]):
        self._args = list(args)

    def __getitem__(self, i):
        return self._args[i]

    def __setitem__(self, i, value):
        self._args[i] = value

    def __delitem__(self, i):
        del self._args[i]

    def __len__(self):
        return len(self._args)

    def insert(self, i, value):
        return self._args.insert(i, value)

    def fill(self, **kwargs):
        result = []
        for i in self._args:
            if isinstance(i, Path):
                result.append(i.string(**kwargs))
            elif isiterable(i):
                arg = ''
                for j in i:
                    if isinstance(j, Path):
                        arg += j.string(**kwargs)
                    else:
                        arg += j
                result.append(arg)
            else:
                result.append(i)
        return result

    def dehydrate(self):
        def dehydrate_each(value):
            if isiterable(value):
                return [auto_dehydrate(i) for i in value]
            return auto_dehydrate(value)

        return [dehydrate_each(i) for i in self]

    @classmethod
    def rehydrate(self, value, **kwargs):
        def rehydrate_each(value):
            if isinstance(value, dict):
                return Path.rehydrate(value, **kwargs)
            elif isiterable(value):
                return tuple(rehydrate_each(i) for i in value)
            return value

        return ShellArguments(rehydrate_each(i) for i in value)

    def __eq__(self, rhs):
        if not isinstance(rhs, ShellArguments):
            return NotImplemented
        return self._args == rhs._args

    def __repr__(self):
        return '<ShellArguments{!r}>'.format(tuple(self._args))


def _wrap_placeholder(split_fn):
    def wrapped(value, *args, **kwargs):
        if isinstance(value, PlaceholderString):
            stashed, placeholders = value.stash()
            args = split_fn(stashed, *args, **kwargs)
            return ShellArguments(
                PlaceholderString.unstash(i, placeholders).unbox(simplify=True)
                for i in args
            )
        return ShellArguments(split_fn(value, *args, **kwargs))

    return wrapped


split_posix = _wrap_placeholder(split_posix_str)
split_windows = _wrap_placeholder(split_windows_str)
split_native = _wrap_placeholder(split_native_str)
