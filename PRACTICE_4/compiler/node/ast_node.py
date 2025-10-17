#!/usr/bin/env python3
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..visitor.ast_visitor import ASTVisitor

class ASTNode(ABC):
    @abstractmethod
    def accept(self, visitor: 'ASTVisitor'):
        pass
