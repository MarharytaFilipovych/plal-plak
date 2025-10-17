#!/usr/bin/env python3
from abc import ABC, abstractmethod
from compiler.context import Context


class ASTNode(ABC):
    @abstractmethod
    def visit(self, context: Context):
        pass
