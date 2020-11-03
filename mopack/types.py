import os
import re
from contextlib import contextmanager
from shlex import shlex
from yaml.error import MarkedYAMLError

from . import iterutils
from .yaml_tools import MarkedDict


_unexpected_kwarg_ex = re.compile(
    r"got an unexpected keyword argument '(\w+)'$"
)

_url_ex = re.compile(
    r'^'
    r'[A-Za-z0-9+.-]+://'        # scheme
    r'(?:[^@:]+(?::[^@:]+)?@)?'  # userinfo (optional)
    r'[^:]+'                     # host
    r'(?::\d{1,5})?'             # port (optional)
    r'(?:[/?#].*)?'              # path
    r'$'
)

_ssh_ex = re.compile(
    r'^'
    r'(?:[^@:]+?@)?'  # username (optional)
    r'[^:]+:'         # host
    r'.+'             # path
    r'$'
)


class FieldError(TypeError):
    def __init__(self, message, field):
        super().__init__(message)
        self.field = field


@contextmanager
def wrap_field_error(field):
    try:
        yield
    except FieldError as e:
        raise FieldError(str(e), (field,) + e.field)


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
def try_load_config(config, context, kind):
    try:
        yield
    except TypeError as e:
        if not isinstance(config, MarkedDict):
            raise

        msg = str(e)
        mark = config.mark
        if isinstance(e, FieldError):
            x = config
            for f in e.field[:-1]:
                x = x[f]
            mark = x.value_marks[e.field[-1]]
        elif type(e) == TypeError:
            m = _unexpected_kwarg_ex.search(msg)
            if m:
                msg = ('{!r} got an unexpected keyword argument {!r}'
                       .format(kind, m.group(1)))
                mark = config.key_marks[m.group(1)]

        raise MarkedYAMLError(context, config.mark, msg, mark)


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
            raise FieldError('expected {}'.format(desc), (field,))

    return check


def constant(*args):
    def check(field, value):
        if value in args:
            return value
        raise FieldError('expected one of {}'.format(
            ', '.join(repr(i) for i in args)
        ), (field,))

    return check


def list_of(other, listify=False):
    def check(field, value):
        if listify:
            value = iterutils.listify(value)
        elif not iterutils.isiterable(value):
            raise FieldError('expected a list', (field,))
        with wrap_field_error(field):
            return [other(i, v) for i, v in enumerate(value)]

    return check


def dict_of(key_type, value_type):
    def check_each(value):
        # Do this here instead of a dict comprehension so we can guarantee that
        # `key_type` is called first.
        for k, v in value.items():
            yield key_type(k, k), value_type(k, v)

    def check(field, value):
        if not isinstance(value, dict):
            raise FieldError('expected a dict', (field,))
        with wrap_field_error(field):
            return {k: v for k, v in check_each(value)}

    return check


def dict_shape(shape, desc):
    def check_item(value, key, check):
        if key in value:
            return check(key, value.get(key, None))
        try:
            return check(key, None)
        except FieldError:
            raise FieldError('expected {}'.format(desc), ())

    def check(field, value):
        if not isinstance(value, dict):
            raise FieldError('expected {}'.format(desc), (field,))
        with wrap_field_error(field):
            for k in value:
                if k not in shape:
                    raise FieldError('unexpected key', (k,))
            return {k: check_item(value, k, sub_check)
                    for k, sub_check in shape.items()}

    return check


def string(field, value):
    if not isinstance(value, str):
        raise FieldError('expected a string', (field,))
    return value


def boolean(field, value):
    if not isinstance(value, bool):
        raise FieldError('expected a boolean', (field,))
    return value


def inner_path(field, value):
    value = string(field, value)
    if os.path.isabs(value) or os.path.splitdrive(value)[0]:
        raise FieldError('expected a relative path', (field,))

    value = os.path.normpath(value)
    if value.split(os.path.sep)[0] == os.path.pardir:
        raise FieldError('expected an inner path', (field,))
    return value


def abs_or_inner_path(field, value):
    value = os.path.normpath(string(field, value))
    if os.path.isabs(value):
        return value

    if value.split(os.path.sep)[0] == os.path.pardir:
        raise FieldError('expected an absolute or inner path', (field,))
    return value


def any_path(base=None):
    def check(field, value):
        value = string(field, value)
        if base:
            value = os.path.join(base, value)
        return os.path.normpath(value)

    return check


def ssh_path(field, value):
    value = string(field, value)
    if not _ssh_ex.match(value):
        raise FieldError('expected an ssh path', (field,))
    return value


def url(field, value):
    value = string(field, value)
    if not _url_ex.match(value):
        raise FieldError('expected a URL', (field,))
    return value


def shell_args(type=list, escapes=False):
    def check(field, value):
        value = string(field, value)

        lexer = shlex(value, posix=True)
        lexer.commenters = ''
        if not escapes:
            lexer.escape = ''
        lexer.whitespace_split = True
        return type(lexer)

    return maybe(one_of(list_of(string), check, desc='shell arguments'), [])
