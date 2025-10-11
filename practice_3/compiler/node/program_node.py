#!/usr/bin/env python3
from ..context import Context
from .ast_node import ASTNode
from .stmt_node import StmtNode
from .return_node import ReturnNode

class ProgramNode(ASTNode):

    def __init__(self, statement_nodes: list[StmtNode], return_node: ReturnNode):
        self.statement_nodes = statement_nodes
        self.return_node = return_node

    def visit(self, context: Context):
        for node in self.statement_nodes:
            node.visit(context)
        self.return_node.visit(context)