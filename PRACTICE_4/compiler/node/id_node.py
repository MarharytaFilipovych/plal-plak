#!/usr/bin/env python3
from .factor_node import FactorNode
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..visitor.ast_visitor import ASTVisitor

class IDNode(FactorNode):
    def __init__(self, variable: str, line: int):
        super().__init__(variable)
        self.line = line

    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_id(self)
