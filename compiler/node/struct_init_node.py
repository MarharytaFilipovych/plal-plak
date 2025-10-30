#!/usr/bin/env python3
from .factor_node import FactorNode
from .expr_node import ExprNode
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..visitor.ast_visitor import ASTVisitor

class StructInitNode(FactorNode):
    def __init__(self, struct_type: str, variable: str, init_expressions: list[ExprNode], line: int):
        super().__init__(variable)
        self.line = line
        self.struct_type = struct_type
        self.init_expressions = init_expressions

    def accept(self, visitor: 'ASTVisitor'):
         return visitor.visit_struct_init(self)
