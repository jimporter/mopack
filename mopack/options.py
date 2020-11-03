from collections import namedtuple

from .types import try_load_config

OptionsSet = namedtuple('OptionsSet', ['common', 'this'])


class BaseOptions:
    def accumulate(self, config):
        kind = getattr(self, self._type_field or 'type')
        with try_load_config(config, self._context, kind):
            return self(**config)
