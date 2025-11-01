#!/usr/bin/env python3
from .factor_node import FactorNode
from .expr_node import ExprNode
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..visitor.ast_visitor import ASTVisitor

class StructInitNode(FactorNode):
    def __init__(self, struct_type: str, init_expressions: list[ExprNode], line: int):
        super().__init__(struct_type)
        self.struct_type = struct_type
        self.init_expressions = init_expressions
        self.line = line

    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_struct_initialization(self)