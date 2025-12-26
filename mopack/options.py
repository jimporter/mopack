import os
from copy import deepcopy

from . import types
from .base_options import BaseOptions
from .builders import BuilderOptions, make_builder_options
from .environment import Environment, env_as_flag
from .freezedried import DictToList, FreezeDried
from .objutils import memoize_method
from .path import Path
from .placeholder import placeholder
from .platforms import platform_name
from .objutils import Unset
from .origins import make_package_options, PackageOptions


class DuplicateSymbolError(ValueError):
    def __init__(self, symbol):
        super().__init__('symbol {!r} already defined'.format(symbol))
        self.symbol = symbol


class ExprSymbols(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__path_bases = ()

    def _ensure_unique_symbols(self, new_symbols):
        for i in new_symbols:
            if i in self:
                raise DuplicateSymbolError(i)

    @property
    def path_bases(self):
        return self.__path_bases

    def best_path_base(self, preferred):
        if preferred in self.__path_bases:
            return preferred
        elif len(self.__path_bases) > 0:
            return self.__path_bases[0]
        else:
            return None

    def augment(self, *, symbols={}, path_bases=[], env=None):
        self._ensure_unique_symbols(symbols.keys())
        self._ensure_unique_symbols(path_bases)
        result = self.copy()

        result.update(symbols)

        result.update({i: placeholder(Path('', i)) for i in path_bases})
        result.__path_bases += tuple(path_bases)
        if env:
            if 'env' not in result:
                result['env'] = Environment()
            result['env'] = result['env'].new_child(env)

        return result

    def copy(self):
        result = ExprSymbols(**self)
        result.__path_bases = self.__path_bases
        return result

    def __copy__(self):
        return self.copy()  # pragma: no cover

    def __deepcopy__(self, memo):
        result = ExprSymbols(**{deepcopy(k, memo): deepcopy(v, memo)
                                for k, v in self.items()})
        result.__path_bases = self.__path_bases
        return result


class CommonOptions(FreezeDried, BaseOptions):
    _context = 'while adding common options'
    type = 'common'
    _version = 2

    @staticmethod
    def upgrade(config, version):
        # v2 adds `auto_link`.
        if version < 2:  # pragma: no cover
            config['auto_link'] = False

        return config

    def __init__(self, deploy_dirs=None):
        self.strict = Unset
        self.target_platform = Unset
        self.auto_link = Unset
        self.env = {}
        self.deploy_dirs = deploy_dirs or {}
        self._finalized = False

    @classmethod
    def rehydrate(cls, config, **kwargs):
        result = super(CommonOptions, cls).rehydrate(config, **kwargs)
        result._finalized = True
        return result

    @staticmethod
    def _fill_env(env, new_env):
        if new_env:
            for k, v in new_env.items():
                if k not in env:
                    env[k] = v
        return env

    def __call__(self, *, strict=None, target_platform=Unset, env=None):
        if self._finalized:
            raise RuntimeError('options are already finalized')

        T = types.TypeCheck(locals(), self._make_expr_symbols())
        if self.strict is Unset and strict is not None:
            T.strict(types.boolean)
        if self.target_platform is Unset:
            T.target_platform(types.maybe(types.string))
        T.env(types.maybe(types.dict_of(types.string, types.string)),
              reducer=self._fill_env)

    def _make_expr_symbols(self):
        deploy_vars = {k: placeholder(Path(v)) for k, v in
                       self.deploy_dirs.items()}

        extra = {'auto_link': self.auto_link} if self._finalized else {}
        return ExprSymbols(
            host_platform=platform_name(),
            target_platform=self.target_platform,
            env=Environment(self.env),
            deploy_dirs=deploy_vars,
            **extra
        )

    def finalize(self):
        if self._finalized:
            raise RuntimeError('CommonOptions already finalized')
        if self.strict is Unset:
            self.strict = False
        if not self.target_platform:
            self.target_platform = platform_name()
        self._fill_env(self.env, os.environ)
        # Set `auto_link` from the environment. XXX: This is a bit awkward and
        # could probably use a better method.
        self.auto_link = env_as_flag('MOPACK_AUTO_LINK', self.env)
        self._finalized = True

    @property
    @memoize_method
    def expr_symbols(self):
        if not self._finalized:
            raise RuntimeError('options not finalized')
        return self._make_expr_symbols()

    def __eq__(self, rhs):
        return (self.target_platform == rhs.target_platform and
                self.env == rhs.env)


@FreezeDried.fields(rehydrate={
    'common': CommonOptions,
    'origins': DictToList[PackageOptions, lambda x: x.origin],
    'builders': DictToList[BuilderOptions, lambda x: x.type],
})
class Options(FreezeDried):
    _option_makers = {'origins': make_package_options,
                      'builders': make_builder_options}
    option_kinds = list(_option_makers.keys())

    def __init__(self, deploy_dirs=None):
        self.common = CommonOptions(deploy_dirs)
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
