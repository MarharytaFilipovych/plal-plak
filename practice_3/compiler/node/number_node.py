#!/usr/bin/env python3
from .factor_node import FactorNode
from ..context import Context


class NumberNode(FactorNode):
    def visit(self, context: Context):
        pass
