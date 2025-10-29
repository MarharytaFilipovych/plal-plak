#!/usr/bin/env python3
from .stmt_node import StmtNode
from .expr_node import ExprNode
from .code_block_node import CodeBlockNode
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..visitor.ast_visitor import ASTVisitor

class IfNode(StmtNode):
    def __init__(self, condition: ExprNode, then_block: CodeBlockNode,
                 else_block: Optional[CodeBlockNode], line: int):
        super().__init__("", condition, line)
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block
        self.line = line

    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_if_statement(self)