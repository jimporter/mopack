import os

from .base_options import BaseOptions
from .builders import BuilderOptions, make_builder_options
from .freezedried import DictToListFreezeDryer, FreezeDried
from .objutils import memoize_method
from .platforms import platform_name
from .sources import make_package_options, PackageOptions
from .types import Unset


class CommonOptions(FreezeDried, BaseOptions):
    _context = 'while adding common options'
    type = 'common'

    def __init__(self):
        self.target_platform = Unset
        self.env = {}

    def __call__(self, *, target_platform=Unset, env=None, **kwargs):
        if self.target_platform is Unset:
            self.target_platform = target_platform
        if env:
            for k, v in env.items():
                if k not in self.env:
                    self.env[k] = v

    def finalize(self):
        self(target_platform=platform_name(), env=os.environ)

    @property
    @memoize_method
    def expr_symbols(self):
        return {
            'host_platform': platform_name(),
            'target_platform': self.target_platform,
            'env': self.env,
        }

    def __eq__(self, rhs):
        return (self.target_platform == rhs.target_platform and
                self.env == rhs.env)


@FreezeDried.fields(rehydrate={
    'common': CommonOptions,
    'sources': DictToListFreezeDryer(PackageOptions, lambda x: x.source),
    'builders': DictToListFreezeDryer(BuilderOptions, lambda x: x.type),
})
class Options(FreezeDried):
    _option_makers = {'sources': make_package_options,
                      'builders': make_builder_options}
    option_kinds = list(_option_makers.keys())
    kind_to_plural = {'source': 'sources',
                      'builder': 'builders'}

    def __init__(self):
        self.common = CommonOptions()
        for i in self.option_kinds:
            setattr(self, i, {})

    def add(self, kind, name):
        opts = self._option_makers[kind](name)
        if opts is not None:
            getattr(self, kind)[name] = opts

    @property
    def expr_symbols(self):
        return self.common.expr_symbols

    @classmethod
    def default(cls):
        opts = cls()
        opts.common.finalize()
        return opts
