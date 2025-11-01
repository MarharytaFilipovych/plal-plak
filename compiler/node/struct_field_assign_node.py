#!/usr/bin/env python3
from .stmt_node import StmtNode
from .struct_field_node import StructFieldNode
from .expr_node import ExprNode
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..visitor.ast_visitor import ASTVisitor

class StructFieldAssignNode(StmtNode):
    def __init__(self, target: StructFieldNode, expr_node: ExprNode, line: int):
        super().__init__(target.field_chain[0], expr_node, line)
        self.target = target

    def accept(self, visitor: 'ASTVisitor'):
        visitor.visit_struct_field_assignment(self)