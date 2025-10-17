#!/usr/bin/env python3
from .expr_node import ExprNode
from ..context import Context
from .factor_node import FactorNode
from ..operator import Operator


class BinaryOpNode(ExprNode):

    def __init__(self, left: FactorNode, operator: Operator, right: FactorNode):
        self.left = left
        self.operator = operator
        self.right = right

    def visit(self, context: Context) -> None:
        self.left.visit(context)
        self.right.visit(context)
