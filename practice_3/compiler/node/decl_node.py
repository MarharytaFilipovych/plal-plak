#!/usr/bin/env python3
from ..context import Context
from .stmt_node import StmtNode
from .expr_node import ExprNode


class DeclNode(StmtNode):

    def __init__(self, variable: str, expr_node: ExprNode, line: int, mutable: bool):
        super().__init__(variable, expr_node, line)
        self.mutable = mutable

    def visit(self, context: Context) -> None:
        if self.variable in context.declared_variables:
            raise ValueError(
                f"Variable '{self.variable}' has already been declared at line {self.line}!!!!!!!!!!")

        context.declared_variables[self.variable] = self.mutable
        context.currently_initializing = self.variable
        self.expr_node.visit(context)
        context.currently_initializing = None
        context.initialized_variables.add(self.variable)
