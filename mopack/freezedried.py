def auto_dehydrate(value, freezedryer=None):
    # If freezedryer is not set, try to dehydrate the value or just return the
    # original value. Otherwise, check if the value is an instance of the
    # freezedryer. If so, dehydrate using the value's `dehydrate()` method; if
    # not, use the freezerdryer's `dehydrate()` method. This lets the value's
    # subtype extend `dehydrate()` if needed.

    if freezedryer is None:
        return value.dehydrate() if hasattr(value, 'dehydrate') else value
    if isinstance(freezedryer, type) and isinstance(value, freezedryer):
        return value.dehydrate()
    return freezedryer.dehydrate(value)


class FreezeDried:
    _type_field = None
    _skip_fields = ()
    _skip_compare_fields = ()
    _rehydrate_fields = {}

    def dehydrate(self):
        if self._type_field is None:
            result = {}
        else:
            result = {self._type_field: getattr(self, self._type_field)}

        for k, v in vars(self).items():
            if k in self._skip_fields:
                continue
            result[k] = auto_dehydrate(v, self._rehydrate_fields.get(k))
        return result

    @classmethod
    def rehydrate(cls, config):
        assert cls != FreezeDried

        if cls._type_field is None:
            this_type = cls
        else:
            typename = config.pop(cls._type_field)
            this_type = cls._get_type(typename)
        result = this_type.__new__(this_type)

        for k, v in config.items():
            if k in this_type._rehydrate_fields and v is not None:
                v = this_type._rehydrate_fields[k].rehydrate(v)
            setattr(result, k, v)

        return result

    def equal(self, rhs, skip_fields=[]):
        def fields(obj):
            return {k: v for k, v in vars(obj).items() if
                    (k not in self._skip_compare_fields and
                     k not in skip_fields)}

        return type(self) == type(rhs) and fields(self) == fields(rhs)

    def __eq__(self, rhs):
        return self.equal(rhs)


class DictKeysFreezeDryer:
    def __init__(self, **kwargs):
        self.keys = kwargs

    def dehydrate(self, value):
        return {k: auto_dehydrate(value[k], type) for k, type in
                self.keys.items()}

    def rehydrate(self, value):
        return {k: type.rehydrate(value[k]) for k, type in self.keys.items()}


class DictToListFreezeDryer:
    def __init__(self, type, key):
        self.type = type
        self.key = key

    def dehydrate(self, value):
        return [auto_dehydrate(i, self.type) for i in value.values()]

    def rehydrate(self, value):
        rehydrated = (self.type.rehydrate(i) for i in value)
        return {self.key(i): i for i in rehydrated}
