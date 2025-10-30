#!/usr/bin/env python3
from abc import ABC, abstractmethod

from ..node.assign_node import AssignNode
from ..node.binary_op_node import BinaryOpNode
from ..node.bool_node import BooleanNode
from ..node.code_block_node import CodeBlockNode
from ..node.decl_node import DeclNode
from ..node.struct_init_node import StructInitNode
from ..node.id_node import IDNode
from ..node.if_node import IfNode
from ..node.number_node import NumberNode
from ..node.program_node import ProgramNode
from ..node.return_node import ReturnNode
from ..node.struct_decl_node import StructDeclNode
from ..node.unary_op_node import UnaryOpNode


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
    def visit_return(self, node: ReturnNode):
        pass

    @abstractmethod
    def visit_binary_operation(self, node: BinaryOpNode):
        pass

    @abstractmethod
    def visit_id(self, node: IDNode):
        pass

    @abstractmethod
    def visit_number(self, node: NumberNode):
        pass

    @abstractmethod
    def visit_boolean(self, node: BooleanNode):
        pass

    @abstractmethod
    def visit_if_statement(self, node: IfNode):
        pass

    @abstractmethod
    def visit_code_block(self, node: CodeBlockNode):
        pass

    @abstractmethod
    def visit_unary_operation(self, node: UnaryOpNode):
        pass

    @abstractmethod
    def visit_struct_decl(self, node: StructDeclNode):
        pass

    @abstractmethod
    def visit_struct_init(self, node: StructInitNode):
        pass
