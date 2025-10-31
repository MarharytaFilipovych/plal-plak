#!/usr/bin/env python3
from .factor_node import FactorNode
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..visitor.ast_visitor import ASTVisitor

class StructFieldNode(FactorNode):
    def __init__(self, field_chain: list[str], line: int):
        super().__init__(field_chain[0])
        self.field_chain = field_chain
        self.line = line
        self.is_mutable = False

    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_struct_field(self)