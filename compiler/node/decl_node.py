#!/usr/bin/env python3
from ..llvm_specifics.data_type import DataType
from .stmt_node import StmtNode
from .expr_node import ExprNode
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..visitor.ast_visitor import ASTVisitor

class DeclNode(StmtNode):
    def __init__(self, variable: str, expr_node: ExprNode, line: int, mutable: bool, data_type: DataType):
        super().__init__(variable, expr_node, line)
        self.mutable = mutable
        self.data_type = data_type

    def accept(self, visitor: 'ASTVisitor'):
        visitor.visit_declaration(self)
