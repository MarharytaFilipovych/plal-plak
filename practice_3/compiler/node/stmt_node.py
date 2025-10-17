#!/usr/bin/env python3
from ..context import Context
from .ast_node import ASTNode
from abc import abstractmethod
from .expr_node import ExprNode


class StmtNode(ASTNode):
    def __init__(self, variable: str, expr_node: ExprNode, line: int):
        self.variable = variable
        self.expr_node = expr_node
        self.line = line

    @abstractmethod
    def visit(self, context: Context):
        pass
