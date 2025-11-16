#!/usr/bin/env python3
from ...llvm_specifics.data_type import DataType
from ...node.decl_node import DeclNode
from ...node.assign_node import AssignNode
from ...node.id_node import IDNode


class VariableAnalyzer:
    def __init__(self, context, parent_visitor):
        self.context = context
        self.parent = parent_visitor

    def visit_declaration(self, node: DeclNode):
        if isinstance(node.data_type, str):
            self._validate_struct_type_exists(node.data_type, node.line)

        if not self.context.declare_variable(node.variable, node.data_type, node.mutable):
            raise ValueError(f"Variable '{node.variable}' has already been declared at line {node.line}!!!!!!!!!!")

        self.context.currently_initializing = node.variable
        expr_type = node.expr_node.accept(self.parent)
        self._check_type_match(expr_type, node.data_type, node.line)
        self.context.currently_initializing = None

    def visit_assignment(self, node: AssignNode):
        self._check_variable_declared(node.variable, node.line)
        self._check_variable_mutable(node.variable, node.line)

        if isinstance(node.expr_node, IDNode) and node.expr_node.value == node.variable:
            raise ValueError(
                f"Self-assignment like '{node.variable} = {node.variable}' is not allowed at line {node.line}!")

        data_type = self.context.get_variable_type(node.variable)
        expr_type = node.expr_node.accept(self.parent)
        self._check_type_match(expr_type, data_type, node.line)

    def visit_id(self, node: IDNode):
        if self.context.currently_initializing == node.value:
            raise ValueError(f"Self-assignment like '{node.value} = {node.value}' is not allowed at line {node.line}!")

        self._check_variable_declared(node.value, node.line)
        return self.context.get_variable_type(node.value)

    def _validate_struct_type_exists(self, type_name: str, line: int):
        if not self.context.is_struct_defined(type_name):
            raise ValueError(f"Type '{type_name}' is not defined at line {line}! "
                             f"Did you forget to declare the struct?")

    def _check_variable_declared(self, var_name: str, line: int):
        if not self.context.is_variable_declared(var_name):
            raise ValueError(f"Variable '{var_name}' not declared at line {line}!")

    def _check_variable_mutable(self, var_name: str, line: int):
        if not self.context.is_variable_mutable(var_name):
            raise ValueError(f"Sorry, but you cannot assign something new to an immutable variable!!! "
                             f"Remove '{var_name}' from line {line}!")

    def _check_type_match(self, expr_type, expected_type, line: int):
        if not self._types_match(expr_type, expected_type):
            raise ValueError(f"Types do not match at line {line}: "
                             f"you cannot assign {expr_type} to {expected_type}! Be careful!")

    def _types_match(self, expr_type, expected_type) -> bool:
        if isinstance(expected_type, DataType) and isinstance(expr_type, DataType):
            return self._is_type_compatible(expr_type, expected_type)
        if isinstance(expected_type, str) and isinstance(expr_type, str):
            return expr_type == expected_type
        return False

    @staticmethod
    def _is_type_compatible(source_type, target_type) -> bool:
        return source_type == target_type or (source_type == DataType.I32 and target_type == DataType.I64)