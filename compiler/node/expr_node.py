#!/usr/bin/env python3
from .ast_node import ASTNode
from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..visitor.ast_visitor import ASTVisitor

class ExprNode(ASTNode):
    @abstractmethod
    def accept(self, visitor: 'ASTVisitor'):
        pass
