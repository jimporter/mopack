import functools
import typing
from itertools import chain
from typing import TypeVar

from .iterutils import each_attr, merge_dicts
from .objutils import Unset


_type_database = {}
_primitives = typing.Union[str, int, float, bool, type(None)]


def freezedryer_for(*types):
    def wrapper(freezedryer):
        for t in types:
            _type_database[t] = freezedryer
        return freezedryer
    return wrapper


def _resolve_freezedryer(freezedryer):
    if hasattr(freezedryer, 'dehydrate'):
        return freezedryer

    origin = typing.get_origin(freezedryer) or freezedryer
    args = typing.get_args(freezedryer)
    return _type_database[origin](origin, *args)


def auto_dehydrate(value, freezedryer=None):
    # If freezedryer is not set, try to dehydrate the value or just return the
    # original value. Otherwise, check if the value is an instance of the
    # freezedryer. If so, dehydrate using the value's `dehydrate()` method;
    # this lets the value's subtype extend `dehydrate()` if needed.
    #
    # Otherwise, try to use the freezedryer's `dehydrate()` method, or look up
    # the freezedryer as a type annotation in our type database.

    if value is None:
        return None
    if freezedryer is None:
        return value.dehydrate() if hasattr(value, 'dehydrate') else value
    if ( isinstance(freezedryer, type) and isinstance(value, freezedryer) and
         hasattr(value, 'dehydrate') ):
        return value.dehydrate()
    return _resolve_freezedryer(freezedryer).dehydrate(value)


def rehydrate(value, freezedryer, **kwargs):
    return _resolve_freezedryer(freezedryer).rehydrate(value, **kwargs)


def _maybe_upgrade_config(cls, config):
    if hasattr(cls, '_version') and '_version' in config:
        version = config.pop('_version')
        if version < cls._version:
            return cls.upgrade(config, version)
        elif version > cls._version:
            raise TypeError(
                'saved version of {!r} exceeds expected version'
                .format(cls.__name__)
            )
    return config


class FreezeDried:
    _rehydrate_fields = {}
    _skip_fields = set()
    _include_fields = set()
    _skip_compare_fields = set()

    def _skipped_field(self, field, compare=False):
        # Don't save private members by default.
        if field.startswith('_') and field not in self._include_fields:
            return True

        skips = self._skip_compare_fields if compare else self._skip_fields
        return field in skips

    @staticmethod
    def fields(*, rehydrate=None, include=None, skip=None, skip_compare=None):
        def wrapper(cls):
            if rehydrate:
                cls._rehydrate_fields = merge_dicts(*chain(
                    each_attr(cls.__bases__, '_rehydrate_fields'), [rehydrate]
                ))
            if include:
                cls._include_fields = set().union(*chain(
                    each_attr(cls.__bases__, '_include_fields'), [include]
                ))
            if skip:
                cls._skip_fields = set().union(*chain(
                    each_attr(cls.__bases__, '_skip_fields'), [skip]
                ))
            if skip_compare:
                cls._skip_compare_fields = set().union(*chain(
                    each_attr(cls.__bases__, '_skip_compare_fields'),
                    [skip_compare]
                ))
            return cls

        return wrapper

    def dehydrate(self, *, extra_data={}):
        result = {**extra_data}
        if hasattr(self, '_version'):
            result['_version'] = self._version

        for k, v in vars(self).items():
            if self._skipped_field(k):
                continue
            result[k] = auto_dehydrate(v, self._rehydrate_fields.get(k))
        return result

    @classmethod
    def rehydrate(cls, config, **kwargs):
        assert cls != FreezeDried

        config = _maybe_upgrade_config(cls, config)
        result = cls.__new__(cls)

        for k, v in config.items():
            if k in cls._rehydrate_fields and v is not None:
                v = rehydrate(v, cls._rehydrate_fields[k], **kwargs)
            setattr(result, k, v)

        return result

    def equal(self, rhs, optional_fields=set()):
        if type(self) is not type(rhs):
            return False

        self_vars, rhs_vars = vars(self), vars(rhs)
        for key in set(self_vars) | set(rhs_vars):
            if self._skipped_field(key, True):
                continue

            self_val = self_vars.get(key, Unset)
            rhs_val = rhs_vars.get(key, Unset)
            if ( key in optional_fields and
                 (self_val is Unset or rhs_val is Unset) ):
                continue
            elif self_val != rhs_val:
                return False

        return True

    def __eq__(self, rhs):
        return self.equal(rhs)


def _generic_rehydrator(fn):
    @functools.wraps(fn)
    def wrapper(cls, config, _found=False, **kwargs):
        # First, find the most-specific type, and call its `rehydrate` method.
        if not _found:
            deduced_type = cls._get_type(config.pop(cls._type_field))
            return deduced_type.rehydrate(
                config, _found=True, **kwargs
            )

        # Next, make sure we've upgraded the config before rehydrating.
        config = _maybe_upgrade_config(cls, config)

        # Now, call the wrapped function, and provide it a helper function to
        # call the parent's `rehydrate` method correctly.
        def rehydrate_parent(parent_cls, config, **kwargs):
            return super(parent_cls, cls).rehydrate.__wrapped__(
                cls, config, rehydrate_parent, **kwargs
            )
        return fn(cls, config, rehydrate_parent, **kwargs)

    return classmethod(wrapper)


class GenericFreezeDried(FreezeDried):
    _type_field = None

    rehydrator = _generic_rehydrator

    def dehydrate(self):
        return super().dehydrate(extra_data={
            self._type_field: getattr(self, self._type_field)
        })

    @_generic_rehydrator
    def rehydrate(cls, config, rehydrate_parent, **kwargs):
        return super(GenericFreezeDried, cls).rehydrate(config, **kwargs)


@freezedryer_for(str, int, float, bool, type(None))
class PrimitiveFreezeDryer:
    def __init__(self, type):
        self.type = type

    def dehydrate(self, value):
        if not isinstance(value, self.type):
            raise TypeError('expected a {}'.format(self.type.__name__))
        return value

    def rehydrate(self, value, **kwargs):
        if not isinstance(value, self.type):
            raise TypeError('expected a {}'.format(self.type.__name__))
        return value


@freezedryer_for(list)
class ListFreezeDryer:
    def __init__(self, type, elem_type):
        self.type = type
        self.elem_type = elem_type

    def dehydrate(self, value):
        if not isinstance(value, self.type):
            raise TypeError('expected a {}'.format(self.type.__name__))
        return [auto_dehydrate(i, self.elem_type) for i in value]

    def rehydrate(self, value, **kwargs):
        return [self.elem_type.rehydrate(i, **kwargs) for i in value]


@freezedryer_for(dict)
class DictFreezeDryer:
    def __init__(self, type, key_type, value_type):
        self.key_type = key_type
        self.value_type = value_type

    def dehydrate(self, value):
        return {auto_dehydrate(k, self.key_type):
                auto_dehydrate(v, self.value_type)
                for k, v in value.items()}

    def rehydrate(self, value, **kwargs):
        return {rehydrate(k, self.key_type, **kwargs):
                rehydrate(v, self.value_type, **kwargs)
                for k, v in value.items()}


@freezedryer_for(typing.Union)
class UnionFreezeDryer:
    def __init__(self, _, *types):
        self.types = types

    def dehydrate(self, value):
        for t in self.types:
            try:
                return auto_dehydrate(value, t)
            except TypeError:
                pass
        raise ValueError('expected one of {}'.format(
            ','.join(t.__name__ for t in self.types)
        ))

    def rehydrate(self, value, **kwargs):
        for t in self.types:
            try:
                return rehydrate(value, t, **kwargs)
            except TypeError:
                pass
        raise ValueError('expected one of {}'.format(
            ','.join(t.__name__ for t in self.types)
        ))


class DictToList(typing.Generic[TypeVar('Type'), TypeVar('Key')]):
    pass


@freezedryer_for(DictToList)
class DictToListFreezeDryer:
    def __init__(self, _, type, key):
        self.type = type
        self.key = key

    def dehydrate(self, value):
        return [auto_dehydrate(i, self.type) for i in value.values()]

    def rehydrate(self, value, **kwargs):
        rehydrated = (rehydrate(i, self.type, **kwargs) for i in value)
        return {self.key(i): i for i in rehydrated}
