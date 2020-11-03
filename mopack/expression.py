import pyparsing as pp
from yaml.error import Mark, MarkedYAMLError

__all__ = ['evaluate', 'ParseException', 'to_yaml_error']

ParseException = pp.ParseException


class Literal:
    def __init__(self, value):
        self.value = value

    def __call__(self, symbols):
        return self.value

    def __repr__(self):
        return '<Literal({!r})>'.format(self.value)


class Symbol:
    def __init__(self, symbol):
        self.symbol = symbol

    def __call__(self, symbols):
        return symbols[self.symbol]

    def __repr__(self):
        return '<Symbol({})>'.format(self.symbol)


class UnaryOp:
    def __init__(self, operator, operand):
        self.operator = operator
        self.operand = operand

    def __call__(self, symbols):
        if self.operator == '!':
            return not self.operand(symbols)
        assert False

    def __repr__(self):
        return '({}{})'.format(self.operator, self.operand)


class BinaryOp:
    def __init__(self, left, operator, right):
        self.operator = operator
        self.left = left
        self.right = right

    def __call__(self, symbols):
        if self.operator == '==':
            return self.left(symbols) == self.right(symbols)
        elif self.operator == '!=':
            return self.left(symbols) != self.right(symbols)
        elif self.operator == '&&':
            return self.left(symbols) and self.right(symbols)
        elif self.operator == '||':
            return self.left(symbols) or self.right(symbols)
        assert False

    def __repr__(self):
        return '({} {} {})'.format(self.left, self.operator, self.right)


string_literal = (pp.QuotedString('"') | pp.QuotedString("'")).setParseAction(
    lambda t: [Literal(t[0])]
)
true_literal = pp.Keyword('true').setParseAction(lambda t: [Literal(True)])
false_literal = pp.Keyword('false').setParseAction(lambda t: [Literal(False)])
bool_literal = true_literal | false_literal
identifier = pp.Word(pp.alphas + '_', pp.alphanums + '_').setParseAction(
    lambda t: [Symbol(t[0])]
)
atom = string_literal | bool_literal | identifier

expr = pp.infixNotation(atom, [
    ('!', 1, pp.opAssoc.RIGHT, lambda t: [UnaryOp(*t[0])]),
    (pp.oneOf('== !='), 2, pp.opAssoc.LEFT, lambda t: [BinaryOp(*t[0])]),
    ('&&', 2, pp.opAssoc.LEFT, lambda t: [BinaryOp(*t[0])]),
    ('||', 2, pp.opAssoc.LEFT, lambda t: [BinaryOp(*t[0])]),
])


def evaluate(symbols, expression):
    return expr.parseString(expression, parseAll=True)[0](symbols)


def to_yaml_error(e, context_mark, mark):
    if not e.pstr:
        found = ''
    elif e.loc >= len(e.pstr):
        found = ', found end of text'
    else:
        found = ', found {!r}'.format(e.pstr[e.loc:e.loc + 1])

    newmark = Mark(mark.name, mark.index + e.loc, mark.line + e.lineno - 1,
                   mark.column + e.column - 1, None, None)
    return MarkedYAMLError('while parsing expression', context_mark,
                           e.msg + found, newmark)
