#!/usr/bin/env python3
from .expr_node import ExprNode
from .factor_node import FactorNode
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..visitor.ast_visitor import ASTVisitor


class UnaryOpNode(ExprNode):
    def __init__(self, operator: str, operand: FactorNode):
        self.operator = operator
        self.operand = operand

    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_unary_operation(self)