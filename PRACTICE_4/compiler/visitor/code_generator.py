#!/usr/bin/env python3
from ..llvm_specifics.boolean import Boolean
from ..llvm_specifics.data_type import DataType
from .ast_visitor import ASTVisitor
from ..node.id_node import IDNode
from ..node.number_node import NumberNode
from ..node.bool_node import BooleanNode
from ..node.binary_op_node import BinaryOpNode
from ..constants import I32_MAX, I32_MIN

class CodeGenerator(ASTVisitor):

    def __init__(self):
        self.variable_versions: dict[str, int] = {}
        self.variable_types: dict[str, DataType] = {}
        self.translated_lines: list[str] = []
        self.temp_counter = 0

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
        reg = self._get_variable_register(node.variable)

        self.variable_types[node.variable] = node.data_type

        expr_type = self._get_node_type(node.expr_node)
        if expr_type == DataType.I32 and node.data_type == DataType.I64:
            temp_reg = self._get_temp_register()
            self.translated_lines.append(f"  {temp_reg} = sext i32 {value} to i64")
            value = temp_reg

        self.translated_lines.append(f"  {reg} = add {llvm_type} 0, {value}")

    def visit_assign(self, node):
        var_type = self.variable_types[node.variable]
        llvm_type = var_type.to_llvm()
        value = node.expr_node.accept(self)
        reg = self._get_variable_register(node.variable)
        expr_type = self._get_node_type(node.expr_node)
        if expr_type == DataType.I32 and var_type == DataType.I64:
            temp_reg = self._get_temp_register()
            self.translated_lines.append(f"  {temp_reg} = sext i32 {value} to i64")
            value = temp_reg

        self.translated_lines.append(f"  {reg} = add {llvm_type} 0, {value}")

    def visit_return(self, node):
        value = node.expr_node.accept(self)
        return_type = self._get_node_type(node.expr_node)
        if return_type == DataType.BOOL:
            cast_reg = self._get_temp_register()
            self.translated_lines.append(f"  {cast_reg} = zext i1 {value} to i32")
            value = cast_reg
        elif return_type == DataType.I64:
            cast_reg = self._get_temp_register()
            self.translated_lines.append(f"  {cast_reg} = trunc i64 {value} to i32")
            value = cast_reg

        self.translated_lines.append(f"  call void @printResult(i32 {value})")
        self.translated_lines.append(f"  ret i32 {value}")

    def visit_binary_operation(self, node):
        left_value = node.left.accept(self)
        right_value = node.right.accept(self)
        
        left_type = self._get_node_type(node.left)
        right_type = self._get_node_type(node.right)
        
        temp_reg = self._get_temp_register()

        if node.operator.is_for_comparison():
            self._generate_comparison(node, left_value, right_value, left_type, right_type, temp_reg)
        else:
            self._generate_arithmetic(node, left_value, right_value, left_type, right_type, temp_reg)

        return temp_reg

    def _generate_comparison(self, node, left_value, right_value, left_type, right_type, temp_reg):
        operand_type = self._infer_operand_type(node.left, node.right)
        
        left_value = self._widen_if_needed(left_value, left_type, operand_type)
        right_value = self._widen_if_needed(right_value, right_type, operand_type)
        
        llvm_op = node.operator.to_llvm()
        self.translated_lines.append(
            f"  {temp_reg} = {llvm_op} {operand_type} {left_value}, {right_value}")

    def _generate_arithmetic(self, node, left_value, right_value, left_type, right_type, temp_reg):
        result_type = node.result_type if node.result_type else DataType.I32
        llvm_type = result_type.to_llvm()
        
        if result_type == DataType.I64:
            left_value = self._widen_if_needed(left_value, left_type, "i64")
            right_value = self._widen_if_needed(right_value, right_type, "i64")
        
        llvm_op = node.operator.to_llvm()
        self.translated_lines.append(
            f"  {temp_reg} = {llvm_op} {llvm_type} {left_value}, {right_value}")

    def _widen_if_needed(self, value, current_type, target_type):
        if target_type == "i64" and current_type == DataType.I32:
            ext_reg = self._get_temp_register()
            self.translated_lines.append(f"  {ext_reg} = sext i32 {value} to i64")
            return ext_reg
        return value
    
    def visit_id(self, node):
        return self._get_current_register(node.value)

    def visit_number(self, node):
        return node.value

    def visit_boolean(self, node):
        return Boolean.from_string(node.value).to_llvm()

    def _get_variable_register(self, variable: str) -> str:
        if variable not in self.variable_versions:
            self.variable_versions[variable] = 0
            return f"%{variable}"
        else:
            self.variable_versions[variable] += 1
            return f"%{variable}.{self.variable_versions[variable]}"

    def _get_current_register(self, variable: str) -> str:
        if variable not in self.variable_versions or self.variable_versions[variable] == 0:
            return f"%{variable}"
        return f"%{variable}.{self.variable_versions[variable]}"

    def _get_temp_register(self) -> str:
        reg = f"%_temp_{self.temp_counter}"
        self.temp_counter += 1
        return reg

    def _infer_operand_type(self, left_node, right_node) -> str:
        left_type = self._get_node_type(left_node)
        right_type = self._get_node_type(right_node)
        
        if left_type == DataType.I64 or right_type == DataType.I64:
            return "i64"
        elif left_type == DataType.I32 or right_type == DataType.I32:
            return "i32"
        else:
            return "i1"

    def _get_node_type(self, node) -> DataType:
        match node:
            case IDNode():
                return self.variable_types[node.value]
            case NumberNode():
                value = int(node.value)
                return DataType.I32 if I32_MIN <= value <= I32_MAX else DataType.I64
            case BooleanNode():
                return DataType.BOOL
            case BinaryOpNode():
                return node.result_type if node.result_type else DataType.I32
            case _:
                return DataType.I32
