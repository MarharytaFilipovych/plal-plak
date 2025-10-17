#!/usr/bin/env python3
from .factor_node import FactorNode
from ..context import Context


class IDNode(FactorNode):
    def __init__(self, variable: str, line: int):
        super().__init__(variable)
        self.line = line

    def visit(self, context: Context):
        if context.currently_initializing == self.value:
            raise ValueError(
                f"Self-assignment like '{self.value} = {self.value}' is not allowed at line {self.line}!")

        if self.value not in context.initialized_variables:
            raise ValueError(
                f"Why did you decide that you are permitted to use uninitialized variables??? "
                f"You placed uninitialized '{self.value}' at line {self.line}!!!")
