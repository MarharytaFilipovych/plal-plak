#!/usr/bin/env python3
from abc import ABC, abstractmethod

from ..llvm_specifics.data_type import DataType
from ..node.assign_node import AssignNode
from ..node.binary_op_node import BinaryOpNode
from ..node.bool_node import BooleanNode
from ..node.decl_node import DeclNode
from ..node.id_node import IDNode
from ..node.number_node import NumberNode
from ..node.program_node import ProgramNode
from ..node.return_node import ReturnNode


class ASTVisitor(ABC):
    @abstractmethod
    def visit_program(self, node: ProgramNode):
        pass

    @abstractmethod
    def visit_declaration(self, node: DeclNode):
        pass

    @abstractmethod
    def visit_assign(self, node: AssignNode):
        pass

    @abstractmethod
    def visit_return(self, node: ReturnNode) -> DataType:
        pass

    @abstractmethod
    def visit_binary_operation(self, node: BinaryOpNode):
        pass

    @abstractmethod
    def visit_id(self, node: IDNode) -> DataType:
        pass

    @abstractmethod
    def visit_number(self, node: NumberNode) -> DataType:
        pass

    @abstractmethod
    def visit_boolean(self, node: BooleanNode) -> DataType:
        pass
