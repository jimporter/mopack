import operator
import pyparsing as pp
from functools import reduce
from pyparsing import ParseBaseException, ParseException

pp.ParserElement.enablePackrat()

__all__ = ['evaluate', 'evaluate_token', 'parse', 'ParseBaseException',
           'ParseException', 'SemanticException', 'Token']


class SemanticException(pp.ParseBaseException):
    pass


class Token:
    pass


class Literal(Token):
    def __init__(self, value):
        self.value = value

    def __call__(self, symbols):
        return self.value

    def __repr__(self):
        return '<Literal({!r})>'.format(self.value)


class Symbol(Token):
    def __init__(self, pstr, loc, symbol):
        self._pstr = pstr
        self.loc = loc
        self.symbol = symbol

    def __call__(self, symbols):
        try:
            return symbols[self.symbol]
        except KeyError:
            msg = 'undefined symbol {!r}'.format(self.symbol)
            raise SemanticException(self._pstr, self.loc, msg)

    def __repr__(self):
        return '<Symbol({})>'.format(self.symbol)


class UnaryOp(Token):
    def __init__(self, operator, operand):
        self.operator = operator
        self.operand = operand

    def __call__(self, symbols):
        if self.operator == '!':
            return not self.operand(symbols)
        assert False

    def __repr__(self):
        return '({}{})'.format(self.operator, self.operand)


class BinaryOp(Token):
    def __init__(self, left, operator, right):
        self.operator = operator
        self.operands = [left, right]

    def __call__(self, symbols):
        if self.operator == '+':
            return self.operands[0](symbols) + self.operands[1](symbols)
        elif self.operator == '==':
            return self.operands[0](symbols) == self.operands[1](symbols)
        elif self.operator == '!=':
            return self.operands[0](symbols) != self.operands[1](symbols)
        elif self.operator == '&&':
            return self.operands[0](symbols) and self.operands[1](symbols)
        elif self.operator == '||':
            return self.operands[0](symbols) or self.operands[1](symbols)
        elif self.operator == '[]':
            return self.operands[0](symbols).get(self.operands[1](symbols))
        assert False

    def __repr__(self):
        return '({} {} {})'.format(self.operands[0], self.operator,
                                   self.operands[1])


class TernaryOp(Token):
    def __init__(self, left, first_operator, middle, second_operator, right):
        self.operator = first_operator + second_operator
        self.operands = [left, middle, right]

    def __call__(self, symbols):
        if self.operator == '?:':
            return (self.operands[1](symbols) if self.operands[0](symbols)
                    else self.operands[2](symbols))
        assert False

    def __repr__(self):
        return '({} {} {}, {})'.format(self.operands[0], self.operator,
                                       *self.operands[1:])


class StringOp(Token):
    def __init__(self, ast):
        self.ast = ast

    def __call__(self, symbols):
        return reduce(operator.add, (
            evaluate_token(symbols, i) for i in self.ast
        ))


expr = pp.Forward()

string_literal = (pp.QuotedString('"') | pp.QuotedString("'")).setParseAction(
    lambda t: [Literal(t[0])]
)
true_literal = pp.Keyword('true').setParseAction(lambda t: [Literal(True)])
false_literal = pp.Keyword('false').setParseAction(lambda t: [Literal(False)])
bool_literal = true_literal | false_literal
null_literal = pp.Keyword('null').setParseAction(lambda t: [Literal(None)])

identifier = pp.Word(pp.alphas + '_', pp.alphanums + '_').setParseAction(
    lambda s, loc, t: [Symbol(s, loc, t[0])]
)
pre_expr = identifier | ('(' + expr + ')').setParseAction(lambda t: t[1])

index = (pre_expr + '[' + expr + ']').setParseAction(
    lambda t: [BinaryOp(t[0], '[]', t[2])]
)

expr_atom = string_literal | bool_literal | null_literal | index | identifier
expr <<= pp.infixNotation(expr_atom, [
    ('!', 1, pp.opAssoc.RIGHT, lambda t: [UnaryOp(*t[0])]),
    ('+', 2, pp.opAssoc.LEFT, lambda t: [BinaryOp(*t[0])]),
    (pp.oneOf('== !='), 2, pp.opAssoc.LEFT, lambda t: [BinaryOp(*t[0])]),
    ('&&', 2, pp.opAssoc.LEFT, lambda t: [BinaryOp(*t[0])]),
    ('||', 2, pp.opAssoc.LEFT, lambda t: [BinaryOp(*t[0])]),
    (('?', ':'), 3, pp.opAssoc.LEFT, lambda t: [TernaryOp(*t[0])]),
])

expr_holder = ('${{' + expr + '}}').setParseAction(lambda t: t[1])
identifier_holder = ('$' + identifier).setParseAction(lambda t: t[1])
escaped_dollar = pp.Literal('$$').setParseAction(lambda t: ['$'])
dollar_expr = escaped_dollar | identifier_holder | expr_holder

bare_string = (pp.SkipTo(pp.Literal('$') | pp.StringEnd()).leaveWhitespace()
               .setParseAction(lambda t: t if len(t[0]) else []))

if_expr = dollar_expr | expr
str_expr = bare_string + (dollar_expr + bare_string)[...]


def evaluate_token(symbols, tok):
    if isinstance(tok, Token):
        return tok(symbols)
    return tok


def parse(expression, if_context=False):
    if if_context:
        return if_expr.parseString(expression, parseAll=True)[0]
    else:
        ast = str_expr.parseString(expression, parseAll=True)
        if len(ast) == 0:
            return expression
        elif len(ast) == 1:
            return ast[0]
        else:
            return StringOp(ast)


def evaluate(symbols, expression, if_context=False):
    return evaluate_token(symbols, parse(expression, if_context))
