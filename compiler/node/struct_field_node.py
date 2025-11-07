#!/usr/bin/env python3
from .factor_node import FactorNode
from typing import TYPE_CHECKING

from ..helpers.field_chain import FieldChain

if TYPE_CHECKING:
    from ..visitor.ast_visitor import ASTVisitor

class StructFieldNode(FactorNode):
    def __init__(self, field_chain: FieldChain, line: int):
        super().__init__(field_chain.fields[0])
        self.field_chain = field_chain
        self.line = line
        self.is_mutable = False

    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_struct_field(self)