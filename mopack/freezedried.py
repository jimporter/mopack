class FreezeDried:
    _type_field = None
    _skip_fields = ()
    _skip_compare_fields = ()
    _rehydrate_fields = {}

    def dehydrate(self):
        result = {self._type_field: getattr(self, self._type_field)}
        for k, v in vars(self).items():
            if k in self._skip_fields:
                continue
            if k in self._rehydrate_fields:
                v = v.dehydrate()
            result[k] = v
        return result

    @classmethod
    def rehydrate(cls, config):
        assert cls != FreezeDried

        typename = config.pop(cls._type_field)
        this_type = cls._get_type(typename)
        result = this_type.__new__(this_type)

        for k, v in config.items():
            if k in this_type._rehydrate_fields:
                v = this_type._rehydrate_fields[k].rehydrate(v)
            setattr(result, k, v)

        return result

    def __eq__(self, rhs):
        def fields(obj):
            return {k: v for k, v in vars(obj).items()
                    if k not in self._skip_compare_fields}

        return type(self) == type(rhs) and fields(self) == fields(rhs)
