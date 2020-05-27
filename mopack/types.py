import os
from contextlib import contextmanager
from shlex import shlex
from yaml.error import MarkedYAMLError

from . import iterutils
from .yaml_tools import MarkedDict


class FieldError(TypeError):
    def __init__(self, message, field):
        super().__init__(message)
        self.field = field


class _UnsetType:
    def __bool__(self):
        return False

    def __eq__(self, rhs):
        return isinstance(rhs, _UnsetType) or rhs is None

    def dehydrate(self):
        return None

    @classmethod
    def rehydrate(self, config):
        if config is not None:
            raise ValueError('expected None')
        return Unset

    def __repr__(self):
        return '<Unset>'


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


def maybe(other, default=None):
    def check(field, value):
        if value is None:
            return default
        return other(field, value)

    return check


def default(other, default=None):
    def check(field, value):
        if value is Unset:
            return default
        return other(field, value)

    return check


def one_of(*args, desc):
    def check(field, value):
        for i in args:
            try:
                return i(field, value)
            except FieldError:
                pass
        else:
            raise FieldError('expected {}'.format(desc), field)

    return check


def constant(*args):
    def check(field, value):
        if value in args:
            return value
        raise FieldError('expected one of {}'.format(
            ', '.join(repr(i) for i in args)
        ), field)

    return check


def list_of(other, listify=False):
    def check(field, value):
        if listify:
            value = iterutils.listify(value)
        elif not iterutils.isiterable(value):
            raise FieldError('expected list', field)
        return [other(field, i) for i in value]

    return check


def dict_shape(shape, desc):
    def check(field, value):
        if ( not isinstance(value, dict) or
             set(value.keys()) != set(shape.keys()) ):
            raise FieldError('expected {}'.format(desc), field)
        return {k: shape[k](field, v) for k, v in value.items()}

    return check


def string(field, value):
    if not isinstance(value, str):
        raise FieldError('expected a string', field)
    return value


def boolean(field, value):
    if not isinstance(value, bool):
        raise FieldError('expected a boolean', field)
    return value


def inner_path(field, value):
    value = string(field, value)
    if os.path.isabs(value) or os.path.splitdrive(value)[0]:
        raise FieldError('expected a relative path', field)

    value = os.path.normpath(value)
    if value.split(os.path.sep)[0] == os.path.pardir:
        raise FieldError('expected an inner path', field)
    return value


def abs_or_inner_path(field, value):
    value = os.path.normpath(string(field, value))
    if os.path.isabs(value):
        return value

    if value.split(os.path.sep)[0] == os.path.pardir:
        raise FieldError('expected an absolute or inner path', field)
    return value


def any_path(base=None):
    def check(field, value):
        value = string(field, value)
        if base:
            value = os.path.join(base, value)
        return os.path.normpath(value)

    return check


def shell_args(type=list, escapes=False):
    def check(field, value):
        value = string(field, value)

        lexer = shlex(value, posix=True)
        lexer.commenters = ''
        if not escapes:
            lexer.escape = ''
        lexer.whitespace_split = True
        return type(lexer)

    return check
