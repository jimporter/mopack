from .types import try_load_config


class BaseOptions:
    def accumulate(self, config):
        with try_load_config(config, self._context):
            return self(**config)
