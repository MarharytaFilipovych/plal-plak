#!/usr/bin/env python3
from ..constants import I32_MAX, I32_MIN
from .ast_visitor import ASTVisitor
from ..context import Context
from ..llvm_specifics.data_type import DataType
from ..node.assign_node import AssignNode
from ..node.binary_op_node import BinaryOpNode
from ..node.bool_node import BooleanNode
from ..node.code_block_node import CodeBlockNode
from ..node.decl_node import DeclNode
from ..node.id_node import IDNode
from ..node.number_node import NumberNode
from ..node.program_node import ProgramNode
from ..node.return_node import ReturnNode
from ..node.unary_op_node import UnaryOpNode
from ..node.struct_decl_node import StructDeclNode
from ..node.struct_init_node import StructInitNode


class SemanticAnalyzer(ASTVisitor):
    def __init__(self):
        self.context = Context()

    def visit_program(self, node: ProgramNode):
        for n in node.statement_nodes:
            n.accept(self)
        node.return_node.accept(self)

    def visit_struct_declaration(self, node: StructDeclNode):
        field_names = set()
        for field in node.fields:
            if field.variable in field_names:
                raise ValueError(f"Duplicate field name '{field.variable}' in struct"
                                 f" '{node.variable}' at line {node.line}! GET RID OF IT!")
            field_names.add(field.variable)

            if not DataType.is_data_type(field.data_type) and not self.context.is_struct_defined(field.data_type):
                raise ValueError(f"The type '{field.data_type}' for field '{field.variable}'"
                                 f" in struct '{node.variable}' at line {node.line} does not exist!")

        self.context.define_struct(node.variable, [(f.data_type, f.variable, f.mutable) for f in node.fields])

    def visit_struct_initialization(self, node: StructInitNode) -> str:
        if not self.context.is_struct_defined(node.struct_type):
            raise ValueError(f"No such struct type '{node.struct_type}' at line {node.line}!")

        struct_fields  = self.context.get_struct_definition(node.struct_type)

        if len(node.init_expressions) != len(struct_fields):
            raise ValueError( f"Struct '{node.struct_type}' expects {len(struct_fields )} fields but you typed {len(node.init_expressions)} at line {node.line}!")

        for i, field in enumerate(struct_fields):
            expr_type = node.init_expressions[i].accept(self)

            if not self.__types_match(expr_type, field.data_type):
                raise ValueError( f"Type mismatch for field '{field.data_type}' in struct '{node.struct_type}': "
                    f"expected {field.data_type}, but you typed {expr_type} at line {node.line}!")

        return node.struct_type

    def visit_declaration(self, node: DeclNode):
        if not self.context.declare_variable(node.variable, node.data_type, node.mutable):
            raise ValueError(f"Variable '{node.variable}' has already been declared at line {node.line}!!!!!!!!!!")

        self.context.currently_initializing = node.variable
        expr_type = node.expr_node.accept(self)

        if not self.__types_match(expr_type, node.data_type):
            raise ValueError( f"Types do not match at line {node.line}: "
                              f"you cannot assign {expr_type} to {node.data_type}! Be careful!")

        self.context.currently_initializing = None

    def visit_assign(self, node: AssignNode):
        if not self.context.is_variable_declared(node.variable):
            raise ValueError(f"Variable '{node.variable}' at line {node.line} is not declared, bro!")

        if not self.context.is_variable_mutable(node.variable):
            raise ValueError(f"Sorry, but you cannot assign something new to an immutable variable!!! "
                             f"Remove '{node.variable}' from line {node.line}!")

        if isinstance(node.expr_node, IDNode) and node.expr_node.value == node.variable:
            raise ValueError(f"Self-assignment like '{node.variable} = {node.variable}'"
                             f" is not allowed at line {node.line}!")

        data_type = self.context.get_variable_type(node.variable)
        expr_type = node.expr_node.accept(self)

        if not self.__types_match(expr_type, data_type):
            raise ValueError(
                f"Types do not match at line {node.line}: you cannot assign {expr_type} to {data_type}! Be careful!")

    def visit_return(self, node: ReturnNode):
        return node.expr_node.accept(self)

    def visit_binary_operation(self, node: BinaryOpNode):
        left_type = node.left.accept(self)
        right_type = node.right.accept(self)

        if node.operator.is_for_comparison():
            if (left_type == DataType.BOOL) != (right_type == DataType.BOOL):
                raise ValueError(f"You cannot compare using {node.operator} boolean with non-boolean!")
            return DataType.BOOL

        if node.operator.is_for_arithmetic():
            if left_type == DataType.BOOL or right_type == DataType.BOOL:
                raise ValueError(f"You cannot play math using {node.operator} on booleans!!!")

            node.result_type = DataType.I64 if (
                        left_type == DataType.I64 or right_type == DataType.I64) else DataType.I32
            return node.result_type

        raise ValueError(f"Where did you take this operator from?: {node.operator}")

    def visit_id(self, node: IDNode):
        if self.context.currently_initializing == node.value:
            raise ValueError(f"Self-assignment like '{node.value} = {node.value}' is not allowed at line {node.line}!")

        if not self.context.is_variable_declared(node.value):
            raise ValueError(
                f"Why did you decide that you are permitted to use uninitialized variables??? "
                f"You placed uninitialized '{node.value}' at line {node.line}!!!")

        return self.context.get_variable_type(node.value)

    def visit_number(self, node: NumberNode) -> DataType:
        value = int(node.value)
        return DataType.I32 if I32_MIN <= value <= I32_MAX else DataType.I64

    def visit_boolean(self, node: BooleanNode) -> DataType:
        return DataType.BOOL

    def visit_if_statement(self, node):
        condition_type = node.condition.accept(self)
        if condition_type != DataType.BOOL:
            raise ValueError(
                f"If condition must be of type bool, but you placed {condition_type} at line {node.line}! How could you????????")

        node.then_block.accept(self)
        if node.else_block:
            node.else_block.accept(self)

    def visit_code_block(self, node: CodeBlockNode):
        self.context.enter_scope()
        for n in node.statements:
            n.accept(self)
        if node.return_node:
            node.return_node.accept(self)
        self.context.exit_scope()

    def visit_unary_operation(self, node: UnaryOpNode) -> DataType:
        operand_type = node.operand.accept(self)
        if node.operator == "!":
            if operand_type != DataType.BOOL:
                raise ValueError(
                    f"The NOT operator (!) can only be applied to the boolean values, dummy,"
                    f"but you applied it to {operand_type}! Do you think it is okay?")
            return DataType.BOOL
        raise ValueError(f"Unknown unary operator: {node.operator}")

    def __types_match(self, expr_type, expected_type) -> bool:
        if isinstance(expected_type, DataType):
            return isinstance(expr_type, DataType) and self.__is_type_compatible(expr_type, expected_type)
        return expr_type == expected_type

    @staticmethod
    def __is_type_compatible(source_type: DataType, target_type: DataType) -> bool:
        return source_type == target_type or (source_type == DataType.I32 and target_type == DataType.I64)