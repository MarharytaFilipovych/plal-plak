#!/usr/bin/env python3
from .factor_node import FactorNode
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..visitor.ast_visitor import ASTVisitor

class BooleanNode(FactorNode):
    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_boolean(self)
