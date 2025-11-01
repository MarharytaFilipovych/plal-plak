#!/usr/bin/env python3
from .stmt_node import StmtNode
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..visitor.ast_visitor import ASTVisitor

class AssignNode(StmtNode):
    def accept(self, visitor: 'ASTVisitor'):
        visitor.visit_assignment(self)