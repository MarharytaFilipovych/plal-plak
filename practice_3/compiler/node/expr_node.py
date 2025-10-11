#!/usr/bin/env python3
from ..context import Context
from .ast_node import ASTNode
from abc import abstractmethod


class ExprNode(ASTNode):
    @abstractmethod
    def visit(self, context: Context):
        pass
