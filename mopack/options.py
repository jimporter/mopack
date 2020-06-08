from collections import namedtuple

from .types import try_load_config

OptionsSet = namedtuple('OptionsSet', ['common', 'this'])


class BaseOptions:
    def accumulate(self, config):
        with try_load_config(config, self._context):
            return self(**config)
