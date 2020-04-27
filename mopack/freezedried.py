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
            if k in self._rehydrate_fields and v is not None:
                v = self._rehydrate_fields[k].dehydrate(v)
            result[k] = v
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


class DictToListFreezeDryer:
    def __init__(self, type, key):
        self.type = type
        self.key = key

    def dehydrate(self, value):
        return [i.dehydrate() for i in value.values()]

    def rehydrate(self, value):
        rehydrated = (self.type.rehydrate(i) for i in value)
        return {self.key(i): i for i in rehydrated}
