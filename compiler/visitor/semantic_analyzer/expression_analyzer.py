#!/usr/bin/env python3
from ...constants import I32_MAX, I32_MIN, NOT
from ...llvm_specifics.data_type import DataType
from ...node.binary_op_node import BinaryOpNode
from ...node.number_node import NumberNode
from ...node.bool_node import BooleanNode
from ...node.unary_op_node import UnaryOpNode


class ExpressionAnalyzer:
    def __init__(self, context, parent_visitor):
        self.context = context
        self.parent = parent_visitor

    @staticmethod
    def visit_number(node: NumberNode) -> DataType:
        value = int(node.value)
        return DataType.I32 if I32_MIN <= value <= I32_MAX else DataType.I64

    @staticmethod
    def visit_boolean(node: BooleanNode) -> DataType:
        return DataType.BOOL

    def visit_binary_operation(self, node: BinaryOpNode):
        left_type = node.left.accept(self.parent)
        right_type = node.right.accept(self.parent)

        self._validate_primitive_types(left_type, right_type, node.operator)

        if node.operator.is_for_comparison():
            return self._compare(left_type, right_type, node.operator)

        if node.operator.is_for_arithmetic():
            return self._do_math(left_type, right_type, node.operator, node)

        raise ValueError(f"Where did you take this operator from?: {node.operator}")

    def visit_unary_operation(self, node: UnaryOpNode) -> DataType:
        operand_type = node.operand.accept(self.parent)
        if node.operator == NOT:
            if operand_type != DataType.BOOL:
                raise ValueError(f"The NOT operator (!) can only be applied to the boolean values, dummy, "
                                 f"but you applied it to {operand_type}! Do you think it is okay?")
            return DataType.BOOL
        raise ValueError(f"Unknown unary operator: {node.operator}")

    @staticmethod
    def _validate_primitive_types(left_type, right_type, operator):
        if not isinstance(left_type, DataType) or not isinstance(right_type, DataType):
            raise ValueError(f'Cannot use operator \'{operator}\' on struct types! '
                             f'Operators only work with primitive types (i32, i64, bool).')

    @staticmethod
    def _compare(left_type: DataType, right_type: DataType, operator) -> DataType:
        if (left_type == DataType.BOOL) != (right_type == DataType.BOOL):
            raise ValueError(f"You cannot compare using {operator} boolean with non-boolean!")
        return DataType.BOOL

    @staticmethod
    def _do_math(left_type: DataType, right_type: DataType, operator, node) -> DataType:
        if left_type == DataType.BOOL or right_type == DataType.BOOL:
            raise ValueError(f"You cannot play math using {operator} on booleans!!!")

        result_type = DataType.I64 if (left_type == DataType.I64 or right_type == DataType.I64) else DataType.I32
        node.result_type = result_type
        return result_type

    def types_match(self, expr_type, expected_type) -> bool:
        if isinstance(expected_type, DataType) and isinstance(expr_type, DataType):
            return self._is_type_compatible(expr_type, expected_type)
        if isinstance(expected_type, str) and isinstance(expr_type, str):
            return expr_type == expected_type
        return False

    @staticmethod
    def _is_type_compatible(source_type: DataType, target_type: DataType) -> bool:
        return source_type == target_type or (source_type == DataType.I32 and target_type == DataType.I64)