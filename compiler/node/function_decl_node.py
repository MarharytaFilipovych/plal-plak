#!/usr/bin/env python3
from typing import TYPE_CHECKING
from .stmt_node import StmtNode
from .code_block_node import CodeBlockNode

if TYPE_CHECKING:
    from ..visitor.ast_visitor import ASTVisitor

class FunctionParam:
    def __init__(self, param_type: str, name: str):
        self.param_type = param_type
        self.name = name

class FunctionDeclNode(StmtNode):
    def __init__(self, func_name: str, params: list[FunctionParam],
                 return_type: str, body: CodeBlockNode, line: int):
        super().__init__(func_name, None, line)
        self.params = params
        self.return_type = return_type
        self.body = body

    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_function_declaration(self)