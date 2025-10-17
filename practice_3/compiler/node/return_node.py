#!/usr/bin/env python3
from ..context import Context
from .ast_node import ASTNode
from .expr_node import ExprNode


class ReturnNode(ASTNode):
    def __init__(self, expr_node: ExprNode):
        self.expr_node = expr_node

    def visit(self, context: Context):
        self.expr_node.visit(context)
