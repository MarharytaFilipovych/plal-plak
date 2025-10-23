#!/usr/bin/env python3
from .expr_node import ExprNode
from ..node.factor_node import FactorNode
from ..llvm_specifics.operator import Operator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..visitor.ast_visitor import ASTVisitor

class BinaryOpNode(ExprNode):
    def __init__(self, left: FactorNode, operator: Operator, right: FactorNode):
        self.left = left
        self.operator = operator
        self.right = right
        self.result_type = None

    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_binary_operation(self)
