#!/usr/bin/env python3
from typing import Optional
from ...constants import GLOBAL_SCOPE
from ...helpers.field_chain import FieldChain
from ...llvm_specifics.data_type import DataType
from ...node.function_decl_node import FunctionDeclNode
from ...node.function_call_node import FunctionCallNode


class FunctionAnalyzer:
    def __init__(self, context, parent_visitor):
        self.context = context
        self.parent = parent_visitor

    def register_function(self, scope: str, node: FunctionDeclNode):
        param_types = [p.param_type for p in node.params]
        self.context.define_function(scope, node.variable, param_types, node.return_type)

    def visit_function_declaration(self, node: FunctionDeclNode, parent):
        self.context.enter_scope()
        self._declare_function_parameters(node)

        if not node.body.return_node:
            raise ValueError(f"Function '{node.variable}' must have a return statement!")

        parent._expected_return_type = self._resolve_type(node.return_type)
        parent._function_name = node.variable

        node.body.accept(parent)

        parent._expected_return_type = None
        parent._function_name = None
        self.context.exit_scope()

    def visit_function_call(self, node: FunctionCallNode, current_struct_context):
        function_scope = self._identify_function_scope(node.field_chain)

        if function_scope == GLOBAL_SCOPE and current_struct_context:
            if self.context.is_function_defined(current_struct_context, node.value):
                function_scope = current_struct_context

        if not self.context.is_function_defined(function_scope, node.value):
            raise ValueError(f"Function '{node.value}' not defined at line {node.line}!")

        func_info = self.context.get_function_info(function_scope, node.value)
        self._validate_argument_count(node, func_info)
        self._validate_argument_types(node, func_info)

        return_type_str = func_info.return_type
        return self._resolve_type(return_type_str)

    def _declare_function_parameters(self, node: FunctionDeclNode):
        for param in node.params:
            param_type = self._resolve_type(param.param_type)
            if not self.context.declare_variable(param.name, param_type, mutable=False):
                raise ValueError(f"Duplicate parameter '{param.name}' in function '{node.variable}'!")

    @staticmethod
    def _validate_argument_count(node: FunctionCallNode, func_info):
        if len(node.arguments) != len(func_info.param_types):
            raise ValueError(f"Function '{node.value}' expects {len(func_info.param_types)} arguments "
                             f"but got {len(node.arguments)} at line {node.line}!")

    def _validate_argument_types(self, node: FunctionCallNode, func_info):
        for i, (arg, expected_type_str) in enumerate(zip(node.arguments, func_info.param_types)):
            arg_type = arg.accept(self.parent)
            expected_type = self._resolve_type(expected_type_str)
            if not self._types_match(arg_type, expected_type):
                raise ValueError(f"Argument {i + 1} to function '{node.value}' has type {arg_type} "
                                 f"but expected {expected_type} at line {node.line}!")

    def _identify_function_scope(self, field_chain: Optional[FieldChain]) -> str:
        if not field_chain:
            return GLOBAL_SCOPE

        current_type = self.context.get_variable_type(field_chain.fields[0])

        for field_name in field_chain.fields[1:]:
            if isinstance(current_type, str):
                struct_fields = self.context.get_struct_definition(current_type)
                field_info = next((f for f in struct_fields if f.variable == field_name), None)
                if field_info:
                    current_type = self._resolve_type(field_info.data_type)
            else:
                break

        return current_type if isinstance(current_type, str) else GLOBAL_SCOPE

    @staticmethod
    def _resolve_type(type_str: str):
        return DataType.from_string(type_str) if DataType.is_data_type(type_str) else type_str

    def _types_match(self, expr_type, expected_type) -> bool:
        if isinstance(expected_type, DataType) and isinstance(expr_type, DataType):
            return self._is_type_compatible(expr_type, expected_type)

        if isinstance(expected_type, str) and isinstance(expr_type, str):
            return expr_type == expected_type

        return False

    @staticmethod
    def _is_type_compatible(source_type: DataType, target_type: DataType) -> bool:
        return source_type == target_type or (source_type == DataType.I32 and target_type == DataType.I64)