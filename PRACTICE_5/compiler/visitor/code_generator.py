#!/usr/bin/env python3
from ..llvm_specifics.boolean import Boolean
from ..llvm_specifics.data_type import DataType
from .ast_visitor import ASTVisitor
from ..node.code_block_node import CodeBlockNode
from ..node.id_node import IDNode
from ..node.if_node import IfNode
from ..node.number_node import NumberNode
from ..node.bool_node import BooleanNode
from ..node.binary_op_node import BinaryOpNode
from ..constants import I32_MAX, I32_MIN
from ..node.unary_op_node import UnaryOpNode


class CodeGenerator(ASTVisitor):

    def __init__(self):
        self.variable_versions: dict[str, int] = {}
        self.variable_types: dict[str, DataType] = {}
        self.translated_lines: list[str] = []
        self.temp_counter = 0
        self.label_counter = 0
        self.max_versions: dict[str, int] = {}

    @staticmethod
    def get_print_function_llvm() -> str:
        return """declare i32 @printf(i8*, ...)

@exit_format = private unnamed_addr constant [29 x i8] c"Program exit with result %d\\0A\\00", align 1

define void @printResult(i32 %val) {
  %fmt_ptr = getelementptr inbounds [29 x i8], [29 x i8]* @exit_format, i32 0, i32 0
  call i32 (i8*, ...) @printf(i8* %fmt_ptr, i32 %val)
  ret void
}

"""

    def visit_program(self, node):
        self.translated_lines = []

        for stmt in node.statement_nodes:
            stmt.accept(self)

        node.return_node.accept(self)

        return "\n".join([
            self.get_print_function_llvm(),
            "define i32 @main() {",
            *self.translated_lines,
            "}"
        ])

    def visit_declaration(self, node): 
        llvm_type = node.data_type.to_llvm()
        value = node.expr_node.accept(self)
        reg = self.__get_variable_register(node.variable)

        self.variable_types[node.variable] = node.data_type

        expr_type = self.__get_node_type(node.expr_node)
        if expr_type == DataType.I32 and node.data_type == DataType.I64:
            temp_reg = self.__get_temp_register()
            self.translated_lines.append(f"  {temp_reg} = sext i32 {value} to i64")
            value = temp_reg

        self.translated_lines.append(f"  {reg} = add {llvm_type} 0, {value}")

    def visit_assign(self, node):
        var_type = self.variable_types[node.variable]
        llvm_type = var_type.to_llvm()
        value = node.expr_node.accept(self)
        reg = self.__get_variable_register(node.variable)
        expr_type = self.__get_node_type(node.expr_node)
        if expr_type == DataType.I32 and var_type == DataType.I64:
            temp_reg = self.__get_temp_register()
            self.translated_lines.append(f"  {temp_reg} = sext i32 {value} to i64")
            value = temp_reg

        self.translated_lines.append(f"  {reg} = add {llvm_type} 0, {value}")

    def visit_return(self, node):
        value = node.expr_node.accept(self)
        return_type = self.__get_node_type(node.expr_node)
        if return_type == DataType.BOOL:
            cast_reg = self.__get_temp_register()
            self.translated_lines.append(f"  {cast_reg} = zext i1 {value} to i32")
            value = cast_reg
        elif return_type == DataType.I64:
            cast_reg = self.__get_temp_register()
            self.translated_lines.append(f"  {cast_reg} = trunc i64 {value} to i32")
            value = cast_reg

        self.translated_lines.append(f"  call void @printResult(i32 {value})")
        self.translated_lines.append(f"  ret i32 {value}")

    def visit_binary_operation(self, node):
        left_value = node.left.accept(self)
        right_value = node.right.accept(self)
        
        left_type = self.__get_node_type(node.left)
        right_type = self.__get_node_type(node.right)
        
        temp_reg = self.__get_temp_register()

        if node.operator.is_for_comparison():
            self.__generate_comparison(node, left_value, right_value, left_type, right_type, temp_reg)
        else:
            self.__generate_arithmetic(node, left_value, right_value, left_type, right_type, temp_reg)

        return temp_reg

    def __generate_comparison(self, node, left_value, right_value, left_type, right_type, temp_reg):
        operand_type = self.__infer_operand_type(node.left, node.right)
        
        left_value = self.__widen_if_needed(left_value, left_type, operand_type)
        right_value = self.__widen_if_needed(right_value, right_type, operand_type)
        
        llvm_op = node.operator.to_llvm()
        self.translated_lines.append(
            f"  {temp_reg} = {llvm_op} {operand_type} {left_value}, {right_value}")

    def __generate_arithmetic(self, node, left_value, right_value, left_type, right_type, temp_reg):
        result_type = node.result_type if node.result_type else DataType.I32
        llvm_type = result_type.to_llvm()
        
        if result_type == DataType.I64:
            left_value = self.__widen_if_needed(left_value, left_type, "i64")
            right_value = self.__widen_if_needed(right_value, right_type, "i64")
        
        llvm_op = node.operator.to_llvm()
        self.translated_lines.append(
            f"  {temp_reg} = {llvm_op} {llvm_type} {left_value}, {right_value}")

    def __widen_if_needed(self, value, current_type, target_type):
        if target_type == "i64" and current_type == DataType.I32:
            ext_reg = self.__get_temp_register()
            self.translated_lines.append(f"  {ext_reg} = sext i32 {value} to i64")
            return ext_reg
        return value
    
    def visit_id(self, node):
        return self.__get_current_register(node.value)

    def visit_number(self, node):
        return node.value

    def visit_boolean(self, node):
        return Boolean.from_string(node.value).to_llvm()

    def __get_variable_register(self, variable: str) -> str:
        if variable not in self.max_versions:
            self.max_versions[variable] = 0
            self.variable_versions[variable] = 0
            return f"%{variable}"
        
        self.max_versions[variable] += 1
        self.variable_versions[variable] = self.max_versions[variable]
        return f"%{variable}.{self.variable_versions[variable]}"

    def __get_current_register(self, variable: str) -> str:
        if variable not in self.variable_versions or self.variable_versions[variable] == 0:
            return f"%{variable}"
        return f"%{variable}.{self.variable_versions[variable]}"

    def __get_temp_register(self) -> str:
        reg = f"%_temp_{self.temp_counter}"
        self.temp_counter += 1
        return reg

    def __infer_operand_type(self, left_node, right_node) -> str:
        left_type = self.__get_node_type(left_node)
        right_type = self.__get_node_type(right_node)
        
        if left_type == DataType.I64 or right_type == DataType.I64:
            return "i64"
        elif left_type == DataType.I32 or right_type == DataType.I32:
            return "i32"
        else:
            return "i1"

    def __get_node_type(self, node) -> DataType:
        if isinstance(node, IDNode):
            return self.variable_types[node.value]
        if isinstance(node, NumberNode):
            value = int(node.value)
            return DataType.I32 if I32_MIN <= value <= I32_MAX else DataType.I64
        if isinstance(node, BooleanNode):
            return DataType.BOOL
        if isinstance(node, BinaryOpNode):
            return node.result_type if node.result_type else DataType.I32
        if isinstance(node, UnaryOpNode):
            return DataType.BOOL
        return DataType.I32

    def visit_if_statement(self, node: IfNode):
        label_id = self.__get_next_label_id()
        then_label, else_label, end_label = self.__generate_if_labels(label_id, node.else_block)

        condition_value = node.condition.accept(self)
        self.translated_lines.append(
            f"  br i1 {condition_value}, label %{then_label}, label %{else_label}")

        self.__emit_block_with_label(node.then_block, then_label, end_label)

        if node.else_block:
            self.__emit_block_with_label(node.else_block, else_label, end_label)

        self._emit_label(end_label)

    def __get_next_label_id(self) -> int:
        label_id = self.label_counter
        self.label_counter += 1
        return label_id

    @staticmethod
    def __generate_if_labels(label_id: int, has_else: bool) -> tuple[str, str, str]:
        then_label = f"then_{label_id}"
        else_label = f"else_{label_id}" if has_else else f"end_{label_id}"
        end_label = f"end_{label_id}"
        return then_label, else_label, end_label

    def __emit_block_with_label(self, block: CodeBlockNode, label: str, end_label: str):
        self._emit_label(label)
        block.accept(self)
        if not block.return_node:
            self.translated_lines.append(f"  br label %{end_label}")

    def _emit_label(self, label: str):
        self.translated_lines.append(f"{label}:")

    def visit_code_block(self, node: CodeBlockNode):
        # Save state before entering block
        saved_versions = self.variable_versions.copy()
        saved_types = self.variable_types.copy()
        
        for n in node.statements:
            n.accept(self)
        if node.return_node:
            node.return_node.accept(self)
        
        self.variable_versions = saved_versions
        self.variable_types = saved_types

    def visit_unary_operation(self, node: UnaryOpNode):
        if node.operator == "!":
            operand = node.operand.accept(self)
            temp_reg = self.__get_temp_register()
            self.translated_lines.append(f"  {temp_reg} = xor i1 {operand}, 1")
            return temp_reg

        raise ValueError(f"We do not support this unary operator: {node.operator}")
