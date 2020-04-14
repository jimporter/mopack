from shlex import shlex


def split(s, type=list, escapes=False):
    if not isinstance(s, str):
        raise TypeError('expected a string')
    lexer = shlex(s, posix=True)
    lexer.commenters = ''
    if not escapes:
        lexer.escape = ''
    lexer.whitespace_split = True
    return type(lexer)
