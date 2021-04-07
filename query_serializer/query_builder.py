import pyparsing as pp
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import Query
from typing import Union, Type, List, Dict, Any
from auto_schema import AutoMarshmallowSchema
from sqlalchemy_filters.filters import Operator, apply_filters
from .constants import STRING_SYMBOL


# Adapted from: https://stackoverflow.com/questions/11133339/parsing-a-complex-logical-expression-in-pyparsing-in-a-binary-tree-fashion
class QueryBuilder(object):
    """
    Class for building a BinaryExpression from string, or vice versa.
    """

    def __init__(self, obj: Type[DeclarativeMeta]):
        self._obj = obj
        self._parser = self._build_parser()
        self._schema = AutoMarshmallowSchema.get_schema(obj)

    @staticmethod
    def _build_parser():
        operator = pp.Regex("|".join(Operator.OPERATORS.keys())).setName("operator")
        comparison_term = (
            pp.pyparsing_common.iso8601_datetime.copy()
            | pp.pyparsing_common.iso8601_date.copy()
            | pp.pyparsing_common.number.copy()
            | pp.QuotedString(STRING_SYMBOL)  # Strings and enums
            | pp.Word(pp.alphas)  # Enums
        )

        condition = pp.Group(pp.pyparsing_common.identifier + operator + comparison_term)

        return pp.infixNotation(condition, [(k, 2, pp.opAssoc.LEFT) for k in ["and", "or"]])

    def _make_dict(self, expr: pp.ParseResults):
        if not isinstance(expr[0], pp.ParseResults):
            attr = getattr(self._obj, expr[0])
            value = self._schema(only=[attr.name]).load({attr.name: expr[2]})[attr.name]

            return [{"field": expr[0], "op": expr[1], "value": value}]

        left = self._make_dict(expr[0])
        right = self._make_dict(expr[2])

        return [{expr[1]: left + right}]

    def to_string(self, expression: Union[BooleanClauseList, BinaryExpression]):
        if isinstance(expression, BooleanClauseList):
            left = self.to_string(expression.clauses[0])
            right = self.to_string(expression.clauses[1])

            # We replace the underscore with empty, as this is for `and`/`or`
            return f"({left} {expression.operator.__name__.replace('_', '')} {right})"

        left = expression.left
        right = expression.right

        value = str(right) if issubclass(left.type.python_type, bool) else right.value
        right_value = self._schema(only=[left.name]).dump({left.name: value})[left.name]

        if issubclass(getattr(self._obj, left.name).type.python_type, str):
            right_value = f"{STRING_SYMBOL}{right_value}{STRING_SYMBOL}"

        return f"({left.name} {expression.operator.__name__} {right_value})"

    def from_string(self, query: Query, expression: str):
        return apply_filters(query, self.string_to_filters(expression))

    def string_to_filters(self, expression: str) -> List[Dict[str, Any]]:
        root = self._parser.parseString(expression)[0]

        return self._make_dict(root)
