import functools
from itertools import chain

from .iterutils import each_attr, merge_dicts


def auto_dehydrate(value, freezedryer=None):
    # If freezedryer is not set, try to dehydrate the value or just return the
    # original value. Otherwise, check if the value is an instance of the
    # freezedryer. If so, dehydrate using the value's `dehydrate()` method; if
    # not, use the freezerdryer's `dehydrate()` method. This lets the value's
    # subtype extend `dehydrate()` if needed.

    if value is None:
        return None
    if freezedryer is None:
        return value.dehydrate() if hasattr(value, 'dehydrate') else value
    if isinstance(freezedryer, type) and isinstance(value, freezedryer):
        return value.dehydrate()
    return freezedryer.dehydrate(value)


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
                v = cls._rehydrate_fields[k].rehydrate(v, **kwargs)
            setattr(result, k, v)

        return result

    def equal(self, rhs, optional_fields=set()):
        if type(self) is not type(rhs):
            return False

        self_vars, rhs_vars = vars(self), vars(rhs)
        for key in set(self_vars) | set(rhs_vars):
            if self._skipped_field(key, True):
                continue
            elif key in self_vars and key in rhs_vars:
                if self_vars[key] != rhs_vars[key]:
                    return False
            elif key in optional_fields:
                continue
            else:
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


class PrimitiveFreezeDryer:
    @staticmethod
    def dehydrate(value):
        assert isinstance(value, (str, int, bool))
        return value

    @staticmethod
    def rehydrate(value, **kwargs):
        return value


class ListFreezeDryer:
    def __init__(self, type):
        self.type = type

    def dehydrate(self, value):
        return [auto_dehydrate(i, self.type) for i in value]

    def rehydrate(self, value, **kwargs):
        return [self.type.rehydrate(i, **kwargs) for i in value]


class DictFreezeDryer:
    def __init__(self, key_type=PrimitiveFreezeDryer,
                 value_type=PrimitiveFreezeDryer):
        self.key_type = key_type
        self.value_type = value_type

    def dehydrate(self, value):
        return {auto_dehydrate(k, self.key_type):
                auto_dehydrate(v, self.value_type)
                for k, v in value.items()}

    def rehydrate(self, value, **kwargs):
        return {self.key_type.rehydrate(k, **kwargs):
                self.value_type.rehydrate(v, **kwargs)
                for k, v in value.items()}


class DictToListFreezeDryer:
    def __init__(self, type, key):
        self.type = type
        self.key = key

    def dehydrate(self, value):
        return [auto_dehydrate(i, self.type) for i in value.values()]

    def rehydrate(self, value, **kwargs):
        rehydrated = (self.type.rehydrate(i, **kwargs) for i in value)
        return {self.key(i): i for i in rehydrated}
