#!/usr/bin/env python3
from typing import TYPE_CHECKING
from .stmt_node import StmtNode
from ..helpers.struct_field import StructField

if TYPE_CHECKING:
    from ..visitor.ast_visitor import ASTVisitor
    from .function_decl_node import FunctionDeclNode

class StructDeclNode(StmtNode):
    def __init__(self, struct_name: str, fields: list[StructField],
                 member_functions: list['FunctionDeclNode'], line: int):
        super().__init__(struct_name, None, line)
        self.line = line
        self.fields = fields
        self.member_functions = member_functions  # NEW

    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_struct_declaration(self)