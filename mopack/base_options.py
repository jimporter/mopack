from .freezedried import GenericFreezeDried
from .types import try_load_config


class BaseOptions:
    def accumulate(self, config, **kwargs):
        kind = getattr(self, getattr(self, '_type_field', 'type'))
        with try_load_config(config, self._context, kind):
            return self(**config, **kwargs)


class OptionsHolder(GenericFreezeDried):
    def __init__(self, options):
        self._options = options

    @GenericFreezeDried.rehydrator
    def rehydrate(cls, config, rehydrate_parent, *, _options, **kwargs):
        result = rehydrate_parent(
            OptionsHolder, config, _options=_options, **kwargs
        )
        result._options = _options
        return result

    @property
    def _common_options(self):
        return self._options.common

    @property
    def _this_options(self):
        name = getattr(self, self._type_field)
        return getattr(self._options, self._options_type).get(name)
