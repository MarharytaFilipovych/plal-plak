#!/usr/bin/env python3
from typing import TYPE_CHECKING
from .stmt_node import StmtNode

if TYPE_CHECKING:
    from ..visitor.ast_visitor import ASTVisitor

class StructField:
    def __init__(self, data_type: str, variable: str, mutable: bool ):
        self.data_type = data_type
        self.variable = variable
        self.mutable = mutable

class StructDeclNode(StmtNode):
    def __init__(self, struct_name: str, fields: list[StructField], line: int):
        super().__init__(struct_name, None, line)
        self.line = line
        self.fields = fields

    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_struct_decl(self)
