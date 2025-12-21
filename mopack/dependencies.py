import re

from .iterutils import iterate
from .objutils import Unset

_bad_dependency_component_ex = re.compile(r'[,[\]]')
_dependency_string_ex = re.compile(
    r'^'
    r'([^,[\]]+)'      # package name
    r'(?:\[('
    r'[^,[\]]+'        # first submodule
    r'(?:,[^,[\]]+)*'  # extra submodules
    r')\])?'
    r'$'
)


class Dependency:
    def __init__(self, name, submodules=Unset):
        if submodules is not Unset:
            def check(s):
                if not s or _bad_dependency_component_ex.search(s):
                    raise ValueError('invalid dependency')
                return s
            self.package = check(name)
            self.submodules = [check(i) for i in iterate(submodules)] or None
        else:
            m = _dependency_string_ex.match(name)
            if not m:
                raise ValueError('invalid dependency')
            self.package, submodules = m.groups()
            if submodules:
                self.submodules = submodules.split(',')
            else:
                self.submodules = None

    def __str__(self):
        if self.submodules:
            return '{}[{}]'.format(self.package, ','.join(self.submodules))
        return self.package

    def __repr__(self):
        return '<Dependency({!r})>'.format(str(self))

    def __eq__(self, rhs):
        return (self.package == rhs.package and
                self.submodules == rhs.submodules)

    def dehydrate(self):
        return str(self)

    @classmethod
    def rehydrate(cls, config, **kwargs):
        return cls(config)
