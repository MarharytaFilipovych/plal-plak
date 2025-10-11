#!/usr/bin/env python3
from ..context import Context
from .id_node import IDNode
from .stmt_node import StmtNode


class AssignNode(StmtNode):
    def visit(self, context: Context):
        if self.variable not in context.declared_variables:
            raise ValueError(
                f"Variable '{self.variable}' at line {self.line} is not declared, bro!")

        if not context.declared_variables[self.variable]:
            raise ValueError(
                f"Sorry, but you cannot assign something new to an immutable "
                f"variable!!! Remove '{self.variable}' from line {self.line}!")

        if isinstance(self.expr_node, IDNode) and self.expr_node.variable == self.variable:
            raise ValueError(
                f"Self-assignment like '{self.variable} = {self.variable}' is not allowed at line {self.line}!"
            )
        self.expr_node.visit(context)
