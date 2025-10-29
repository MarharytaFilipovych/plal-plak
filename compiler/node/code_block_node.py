#!/usr/bin/env python3
from .ast_node import ASTNode
from .return_node import ReturnNode
from .stmt_node import StmtNode
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..visitor.ast_visitor import ASTVisitor

class CodeBlockNode(ASTNode):
    def __init__(self, statements: list[StmtNode],
                 return_node: Optional[ReturnNode], scope_id: int):
        self.statements = statements
        self.return_node = return_node
        self.scope_id = scope_id

    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_code_block(self)
