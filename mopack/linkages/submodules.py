import warnings

from .. import expression as expr, types
from ..iterutils import ismapping
from ..placeholder import placeholder as _placeholder


class SubmodulePlaceholder:
    pass


placeholder = SubmodulePlaceholder()
variable = _placeholder(placeholder)
expr_symbols = {'submodule': variable}


def evaluate_if(symbols, expression, submodule_name):
    if isinstance(expression, bool):
        return expression
    symbols = symbols.augment(symbols={'submodule': submodule_name})
    return expr.evaluate(symbols, expression, if_context=True)


# TODO: Remove these after v0.2 is released.
def _migrate_submodule_map(submodule_map, *, mangle=False):
    if ismapping(submodule_map):
        return [{'_if' if mangle else 'if':
                 True if k == '*' else 'submodule == {!r}'.format(k),
                 **v} for k, v in submodule_map.items()]
    return submodule_map


def migrate_submodule_map(submodule_map):
    warnings.warn(types.FieldKeyWarning(
        '`submodule_map` is deprecated; use `submodule_linkage` instead',
        'usage'
    ))
    return _migrate_submodule_map(submodule_map)


def migrate_saved_submodule_map(submodule_map):
    return _migrate_submodule_map(submodule_map, mangle=True)
