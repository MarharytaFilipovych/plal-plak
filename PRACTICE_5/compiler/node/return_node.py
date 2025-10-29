#!/usr/bin/env python3
from .ast_node import ASTNode
from .expr_node import ExprNode
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..visitor.ast_visitor import ASTVisitor

class ReturnNode(ASTNode):
    def __init__(self, expr_node: ExprNode):
        self.expr_node = expr_node

    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_return(self)
