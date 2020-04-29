import os
from contextlib import contextmanager
from shlex import shlex
from yaml.error import MarkedYAMLError

from .yaml_tools import MarkedDict


class FieldError(TypeError):
    def __init__(self, message, field):
        super().__init__(message)
        self.field = field


class _UnsetType:
    def __bool__(self):
        return False

    def dehydrate(self):
        return None

    @classmethod
    def rehydrate(self, config):
        if config is not None:
            raise ValueError('expected None')
        return Unset


Unset = _UnsetType()


@contextmanager
def try_load_config(config, context):
    try:
        yield
    except TypeError as e:
        if not isinstance(config, MarkedDict):
            raise

        mark = (config.marks[e.field] if isinstance(e, FieldError)
                else config.mark)
        raise MarkedYAMLError(context, config.mark, str(e), mark)


def inner_path(field, p, none_ok=True):
    if none_ok and p is None:
        return None
    if not isinstance(p, str):
        raise FieldError('expected a string', field)
    if os.path.isabs(p) or os.path.splitdrive(p)[0]:
        raise FieldError('expected a relative path', field)

    p = os.path.normpath(p)
    if p.split(os.path.sep)[0] == os.path.pardir:
        raise FieldError('expected an inner path', field)
    return p


def shell_args(field, s, type=list, escapes=False, none_ok=True):
    if none_ok and s is None:
        return []
    if not isinstance(s, str):
        raise FieldError('expected a string', field)

    lexer = shlex(s, posix=True)
    lexer.commenters = ''
    if not escapes:
        lexer.escape = ''
    lexer.whitespace_split = True
    return type(lexer)
