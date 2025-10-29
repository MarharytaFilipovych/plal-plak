#!/usr/bin/env python3
from abc import abstractmethod
from .expr_node import ExprNode
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..visitor.ast_visitor import ASTVisitor

class FactorNode(ExprNode):
    def __init__(self, value: str):
        self.value = value

    @abstractmethod
    def accept(self, visitor: 'ASTVisitor'):
        pass
