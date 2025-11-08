#!/usr/bin/env python3
from typing import Union
from ...llvm_specifics.data_type import DataType
from ...node.id_node import IDNode
from ...node.number_node import NumberNode
from ...node.bool_node import BooleanNode
from ...node.binary_op_node import BinaryOpNode
from ...node.unary_op_node import UnaryOpNode
from ...node.struct_init_node import StructInitNode
from ...node.struct_field_node import StructFieldNode
from ...node.function_call_node import FunctionCallNode
from ...constants import I32_MAX, I32_MIN


class TypeConverter:
    def __init__(self, variable_registry, struct_ops, function_return_types: dict):
        self.variable_registry = variable_registry
        self.struct_ops = struct_ops
        self.function_return_types = function_return_types

    def get_node_type(self, node) -> Union[DataType, str]:
        if isinstance(node, IDNode):
            return self.variable_registry.get_variable_type(node.value)
        if isinstance(node, NumberNode):
            value = int(node.value)
            return DataType.I32 if I32_MIN <= value <= I32_MAX else DataType.I64
        if isinstance(node, BooleanNode):
            return DataType.BOOL
        if isinstance(node, BinaryOpNode):
            if node.operator.is_for_comparison():
                return DataType.BOOL
            return node.result_type if node.result_type else DataType.I32
        if isinstance(node, UnaryOpNode):
            return DataType.BOOL
        if isinstance(node, StructInitNode):
            return node.struct_type
        if isinstance(node, StructFieldNode):
            return self._get_struct_field_type(node)
        if isinstance(node, FunctionCallNode):
            return self._get_function_return_type(node)
        return DataType.I32

    def _get_struct_field_type(self, node: StructFieldNode) -> Union[DataType, str]:
        current_type = self.variable_registry.get_variable_type(node.field_chain.fields[0])

        for i in range(1, len(node.field_chain.fields)):
            if isinstance(current_type, str):
                fields = self.struct_ops.struct_definitions[current_type]
                field_info = next((f for f in fields if f[0] == node.field_chain.fields[i]), None)
                if field_info:
                    field_data_type = field_info[2]
                    current_type = (DataType.from_string(field_data_type)
                                    if DataType.is_data_type(field_data_type)
                                    else field_data_type)

        return current_type

    def _get_function_return_type(self, node: FunctionCallNode) -> Union[DataType, str]:
        if node.field_chain:
            struct_type = self.get_object_type_from_chain(node.field_chain.fields)
            mangled_name = f"{struct_type}_{node.value}"
            func_return_type = self.function_return_types.get(mangled_name, "i32")
        else:
            func_return_type = self.function_return_types.get(node.value, "i32")
        return DataType.from_string(func_return_type) if DataType.is_data_type(func_return_type) else func_return_type

    def get_object_type_from_chain(self, object_chain: list[str]) -> str:
        current_type = self.variable_registry.get_variable_type(object_chain[0])

        for i in range(1, len(object_chain)):
            if isinstance(current_type, str):
                fields = self.struct_ops.struct_definitions[current_type]
                field_info = next((f for f in fields if f[0] == object_chain[i]), None)
                if field_info:
                    field_data_type = field_info[2]
                    current_type = (DataType.from_string(field_data_type)
                                    if DataType.is_data_type(field_data_type)
                                    else field_data_type)

        return current_type

    @staticmethod
    def get_llvm_type(type_name: str) -> str:
        if DataType.is_data_type(type_name):
            return DataType.from_string(type_name).to_llvm()
        return f"%struct.{type_name}"

    def infer_operand_type(self, left_node, right_node) -> str:
        left_type = self.get_node_type(left_node)
        right_type = self.get_node_type(right_node)

        if left_type == DataType.I64 or right_type == DataType.I64:
            return "i64"
        elif left_type == DataType.I32 or right_type == DataType.I32:
            return "i32"
        else:
            return "i1"