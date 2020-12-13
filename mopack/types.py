import os
import re
from contextlib import contextmanager
from yaml.error import MarkedYAMLError

from . import iterutils
from .exceptions import ConfigurationError
from .path import Path
from .shell import split_posix
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


class FieldError(TypeError, ConfigurationError):
    def __init__(self, message, field):
        super().__init__(message)
        self.field = iterutils.listify(field, type=tuple)


class FieldKeyError(FieldError):
    pass


class FieldValueError(FieldError):
    pass


def kwarg_error_to_field_error(e, kind):
    if type(e) == TypeError:
        m = _unexpected_kwarg_ex.search(str(e))
        if m:
            msg = ('{} got an unexpected keyword argument {!r}'
                   .format(kind, m.group(1)))
            return FieldKeyError(msg, m.group(1))
    return e


@contextmanager
def wrap_field_error(field, kind=None):
    try:
        yield
    except TypeError as e:
        e = kwarg_error_to_field_error(e, kind) if kind else e
        if not isinstance(e, FieldError):
            raise e
        new_field = iterutils.listify(field, type=tuple) + e.field
        raise type(e)(str(e), new_field)


@contextmanager
def ensure_field_error(field):
    try:
        yield
    except Exception as e:
        if isinstance(e, FieldError):
            raise
        raise FieldValueError(str(e), field)


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

        e = kwarg_error_to_field_error(e, kind)
        msg = str(e)
        mark = config.mark
        if isinstance(e, FieldError):
            x = config
            for f in e.field[:-1]:
                x = x[f]
            marks = (x.key_marks if isinstance(e, FieldKeyError)
                     else x.value_marks)
            mark = marks[e.field[-1]]

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
            except FieldValueError:
                pass
        else:
            raise FieldValueError('expected {}'.format(desc), field)

    return check


def constant(*args):
    def check(field, value):
        if value in args:
            return value
        raise FieldValueError('expected one of {}'.format(
            ', '.join(repr(i) for i in args)
        ), field)

    return check


def list_of(other, listify=False):
    def check(field, value):
        if listify:
            value = iterutils.listify(value)
        elif not iterutils.isiterable(value):
            raise FieldValueError('expected a list', field)
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
            raise FieldValueError('expected a dict', field)
        with wrap_field_error(field):
            return {k: v for k, v in check_each(value)}

    return check


def dict_shape(shape, desc):
    def check_item(value, key, check):
        if key in value:
            return check(key, value.get(key, None))
        try:
            return check(key, None)
        except FieldValueError:
            raise FieldValueError('expected {}'.format(desc), ())

    def check(field, value):
        if not isinstance(value, dict):
            raise FieldValueError('expected {}'.format(desc), field)
        with wrap_field_error(field):
            for k in value:
                if k not in shape:
                    raise FieldValueError('unexpected key', k)
            return {k: check_item(value, k, sub_check)
                    for k, sub_check in shape.items()}

    return check


def string(field, value):
    if not isinstance(value, str):
        raise FieldValueError('expected a string', field)
    return value


def boolean(field, value):
    if not isinstance(value, bool):
        raise FieldValueError('expected a boolean', field)
    return value


def path_fragment(field, value):
    value = string(field, value)
    if os.path.isabs(value) or os.path.splitdrive(value)[0]:
        raise FieldValueError('expected a relative path', field)

    value = os.path.normpath(value)
    if value.split(os.path.sep)[0] == os.path.pardir:
        raise FieldValueError('expected an inner path', field)
    return value


def abs_or_inner_path(*bases):
    def check(field, value):
        with ensure_field_error(field):
            value = Path.ensure_path(value, bases + ('absolute',))
            if not value.is_abs() and not value.is_inner():
                raise FieldValueError('expected an absolute or inner path',
                                      field)
            return value

    return check


def any_path(*bases):
    def check(field, value):
        with ensure_field_error(field):
            return Path.ensure_path(value, bases + ('absolute',))

    return check


def ssh_path(field, value):
    value = string(field, value)
    if not _ssh_ex.match(value):
        raise FieldValueError('expected an ssh path', field)
    return value


def url(field, value):
    value = string(field, value)
    if not _url_ex.match(value):
        raise FieldValueError('expected a URL', field)
    return value


def shell_args(type=list, escapes=False):
    def check(field, value):
        return split_posix(string(field, value), type, escapes)

    return maybe(one_of(list_of(string), check, desc='shell arguments'), [])
