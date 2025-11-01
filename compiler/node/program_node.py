#!/usr/bin/env python3
from .function_decl_node import FunctionDeclNode
from .struct_decl_node import StructDeclNode
from ..node.ast_node import ASTNode
from ..node.return_node import ReturnNode
from ..node.stmt_node import StmtNode
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..visitor.ast_visitor import ASTVisitor

class ProgramNode(ASTNode):
    def __init__(self, struct_decls: list[StructDeclNode], func_decls: list[FunctionDeclNode],
                 statement_nodes: list[StmtNode], return_node: ReturnNode):
        self.struct_decls = struct_decls
        self.func_decls = func_decls
        self.statement_nodes = statement_nodes
        self.return_node = return_node

    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_program(self)