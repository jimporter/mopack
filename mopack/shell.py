from collections.abc import MutableSequence
from enum import Enum
from shlex import shlex

from .platforms import platform_name


_Token = Enum('Token', ['char', 'quote', 'space'])
_State = Enum('State', ['between', 'char', 'word', 'quoted'])


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


def split_windows(s, type=list):
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


def split_posix(s, type=list, escapes=False):
    if not isinstance(s, str):
        raise TypeError('expected a string')
    lexer = shlex(s, posix=True)
    lexer.commenters = ''
    if not escapes:
        lexer.escape = ''
    lexer.whitespace_split = True
    return type(lexer)


def split_native(s, type=list):
    if platform_name() == 'windows':
        return split_windows(s, type)
    return split_posix(s, type)


def get_cmd(env, cmdvar, default):
    return split_native(env.get(cmdvar, default))
