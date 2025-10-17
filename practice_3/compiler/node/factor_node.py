#!/usr/bin/env python3
from ..context import Context
from abc import abstractmethod
from .expr_node import ExprNode


class FactorNode(ExprNode):
    def __init__(self, value: str):
        self.value = value

    @abstractmethod
    def visit(self, context: Context):
        pass
