#!/usr/bin/env python3
from ..node.ast_node import ASTNode
from abc import abstractmethod
from .expr_node import ExprNode
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..visitor.ast_visitor import ASTVisitor

class StmtNode(ASTNode):
    def __init__(self, variable: str, expr_node: ExprNode, line: int):
        self.variable = variable
        self.expr_node = expr_node
        self.line = line

    @abstractmethod
    def accept(self, visitor: 'ASTVisitor'):
        pass
