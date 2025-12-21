import warnings
from typing import List

from .. import types
from ..dependencies import Dependency
from ..freezedried import FreezeDried
from ..iterutils import ismapping
from ..types import Unset


class ManagedSubmoduleProps(FreezeDried):
    def __init__(self, symbols):
        pass


@FreezeDried.fields(rehydrate={'dependencies': List[Dependency]})
class UnmanagedSubmoduleProps(FreezeDried):
    def __init__(self, symbols, *, dependencies=Unset):
        T = types.TypeCheck(locals(), symbols)
        T.dependencies(types.maybe(types.list_of(
            types.dependency, listify=True
        ), default=[]))


def _submodule_props_type(symbols, type):
    def check(field, value):
        with types.wrap_field_error(field):
            return type(symbols, **types.mangle_keywords(value or {}))

    return check


def submodules_type(symbols, base_type, *, raw=False):
    maybe = types.maybe_raw if raw else types.maybe
    return maybe(types.one_of(
        types.dict_of(types.string, _submodule_props_type(symbols, base_type)),
        types.constant('*'),
        desc='a dictionary of submodules'
    ))


def submodule_required_type(submodules, *, raw=False):
    if submodules is Unset:
        default = None
        t = types.one_of(types.boolean, types.constant(None),
                         desc='a boolean or null')
    elif submodules:
        default = True
        t = types.boolean
    else:  # not submodules
        default = None
        t = types.constant(None)

    if raw:
        return types.maybe_raw(t, empty=(Unset,))
    else:
        return types.maybe(t, default=default, empty=(Unset,))


# TODO: Remove this after v0.2 is released.
def migrate_submodules(submodules, submodule_required):
    if ( ismapping(submodules) and
         set(submodules.keys()) == {'names', 'required'} ):
        warnings.warn(types.FieldKeyWarning(
            ('`submodules` now takes a dictionary of submodules; use ' +
             '`submodule_required` to set whether submodules are ' +
             'required instead'), 'submodules'
        ))
        submodule_required = submodules.get('required', True)
        submodules = {i: {} for i in submodules['names']}
    return submodules, submodule_required


def migrate_saved_submodules(config, managed=False):
    if config['submodules']:
        config['submodule_required'] = config['submodules']['required']
        config['submodules'] = {
            i: ({} if managed else {'dependencies': []})
            for i in config['submodules']['names']
        }
