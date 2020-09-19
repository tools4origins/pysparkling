import ast

from pysparkling.sql.expressions.operators import Equal, Invert, LessThan, LessThanOrEqual, GreaterThan, \
    GreaterThanOrEqual, Add, Minus, Time, Divide, Mod, Cast, And, BitwiseAnd, BitwiseOr, BitwiseXor, Or
from pysparkling.sql.functions import concat
from pysparkling.sql.types import DoubleType, StringType


class SqlParsingError(Exception):
    pass


def check_children(expected, children):
    if len(children) != expected:
        raise SqlParsingError("Expecting {0} children, got {1}: {2}".format(expected, len(children), children))


def unwrap(*children):
    check_children(1, children)
    return convert_tree(children[0])


def empty(*children):
    check_children(0, children)


def first_child_only(*children):
    return convert_tree(children[0])


def child_and_eof(*children):
    check_children(2, children)
    return convert_tree(children[0])


def convert_tree(tree):
    tree_type = tree.__class__.__name__
    print(tree_type)
    if not hasattr(tree, "children"):
        return get_leaf_value(tree)
    converter = CONVERTERS[tree_type]
    return converter(*tree.children)


def binary_operation(*children):
    check_children(3, children)
    left, operator, right = children
    cls = binary_operations[convert_tree(operator)]
    return cls(
        convert_tree(left),
        convert_tree(right)
    )


def parenthesis_context(*children):
    check_children(3, children)
    return convert_tree(children[1])


def get_leaf_value(*children):
    check_children(1, children)
    value = children[0]
    if value.__class__.__name__ != "TerminalNodeImpl":
        raise Exception("Expecting TerminalNodeImpl, got {0}".format(value.__class__.__name__))
    if not hasattr(value, "symbol"):
        raise Exception("Got leaf value but without symbol")
    return value.symbol.text


def explicit_list(*children):
    return tuple(
        convert_tree(c)
        for c in children[1:-1:2]
    )


def implicit_list(*children):
    return tuple(
        convert_tree(c)
        for c in children[::2]
    )


def concat_to_literal(*children):
    return ast.literal_eval("".join(convert_tree(c) for c in children))


CONVERTERS = {
    "SingleStatementContext": first_child_only,
    "SingleExpressionContext": child_and_eof,
    "SingleTableIdentifierContext": child_and_eof,
    "SingleMultipartIdentifierContext": child_and_eof,
    "SingleFunctionIdentifierContext": child_and_eof,
    "SingleDataTypeContext": child_and_eof,
    "SingleTableSchemaContext": child_and_eof,
    'NamespaceContext': get_leaf_value,
    'SetQuantifierContext': get_leaf_value,
    'ComparisonOperatorContext': get_leaf_value,
    'ArithmeticOperatorContext': get_leaf_value,
    'PredicateOperatorContext': get_leaf_value,
    'BooleanValueContext': get_leaf_value,
    'QuotedIdentifierContext': get_leaf_value,
    'AnsiNonReservedContext': get_leaf_value,
    'StrictNonReservedContext': get_leaf_value,
    'NonReservedContext': get_leaf_value,
    'TerminalNodeImpl': get_leaf_value,
    'DescribeFuncNameContext': unwrap,
    'TablePropertyValueContext': unwrap,
    'TransformArgumentContext': unwrap,
    'ExpressionContext': unwrap,
    'IntervalUnitContext': unwrap,
    'FunctionNameContext': unwrap,
    'ExponentLiteralContext': concat_to_literal,
    'DecimalLiteralContext': concat_to_literal,
    'LegacyDecimalLiteralContext': concat_to_literal,
    'IntegerLiteralContext': concat_to_literal,
    'BigIntLiteralContext': concat_to_literal,
    'SmallIntLiteralContext': concat_to_literal,
    'TinyIntLiteralContext': concat_to_literal,
    'DoubleLiteralContext': concat_to_literal,
    'BigDecimalLiteralContext': concat_to_literal,
    'NumberContext': concat_to_literal,
    'TablePropertyListContext': explicit_list,
    'ConstantListContext': explicit_list,
    'NestedConstantListContext': explicit_list,
    'IdentifierListContext': explicit_list,
    'OrderedIdentifierListContext': explicit_list,
    'IdentifierCommentListContext': explicit_list,
    'TransformListContext': explicit_list,
    'AssignmentListContext': implicit_list,
    'MultipartIdentifierListContext': implicit_list,
    'QualifiedColTypeWithPositionListContext': implicit_list,
    'ColTypeListContext': implicit_list,
    'ComplexColTypeListContext': implicit_list,
    'QualifiedNameListContext': implicit_list,
    "ComparisonContext": binary_operation,
    "ArithmeticBinaryContext": binary_operation,
    "LogicalBinaryContext": binary_operation,
    "RealIdentContext": empty,
    "ParenthesizedExpressionContext": parenthesis_context,
    # WIP!
    # todo: check that all context are there
    #  including yyy: definition
    #  and definition #xxx
    "NamedExpressionContext": unwrap,
    "PredicatedContext": unwrap,
    "ValueExpressionDefaultContext": unwrap,
    "ColumnReferenceContext": unwrap,
    "IdentifierContext": unwrap,
    "ConstantDefaultContext": unwrap,
    "NumericLiteralContext": unwrap,
    "QuotedIdentifierAlternativeContext": unwrap,
    "UnquotedIdentifierContext": get_leaf_value,
    "StringLiteralContext": get_leaf_value,
}

binary_operations = {
    "=": Equal,
    "==": Equal,
    "<>": lambda *args: Invert(Equal(*args)),
    "!=": lambda *args: Invert(Equal(*args)),
    "<": LessThan,
    "<=": LessThanOrEqual,
    "!>": LessThanOrEqual,
    ">": GreaterThan,
    ">=": GreaterThanOrEqual,
    "!<": GreaterThanOrEqual,
    "+": Add,
    "-": Minus,
    '*': Time,
    '/': lambda a, b: Divide(Cast(a, DoubleType), Cast(b, DoubleType)),
    '%': Mod,
    'DIV': lambda a, b: Divide(Cast(a, DoubleType), Cast(b, DoubleType)),
    '&': BitwiseAnd,
    '|': BitwiseOr,
    '||': lambda a, b: concat(Cast(a, StringType), Cast(b, StringType)),
    '^': BitwiseXor,
    'AND': And,
    'OR': Or,
}
