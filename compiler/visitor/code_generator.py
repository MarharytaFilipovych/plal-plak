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
from ..constants import I32_MAX, I32_MIN, NOT
from ..node.struct_decl_node import StructDeclNode
from ..node.struct_init_node import StructInitNode
from ..node.struct_field_node import StructFieldNode
from ..node.struct_field_assign_node import StructFieldAssignNode
from ..node.function_decl_node import FunctionDeclNode
from ..node.function_call_node import FunctionCallNode
from ..node.unary_op_node import UnaryOpNode
from typing import Union


class CodeGenerator(ASTVisitor):

    def __init__(self):
        self.variable_versions: dict[str, int] = {}
        self.variable_types: dict[str, Union[DataType, str]] = {}
        self.translated_lines: list[str] = []
        self.temp_counter = 0
        self.label_counter = 0
        self.max_versions: dict[str, int] = {}

        self.struct_definitions: dict[str, list] = {}
        self.struct_type_lines: list[str] = []
        self.function_definitions: list[str] = []
        self.in_function: bool = False

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
        self.__reset_state()

        for struct_decl in node.struct_decls:
            struct_decl.accept(self)

        for func_decl in node.func_decls:
            func_decl.accept(self)

        for stmt in node.statement_nodes:
            stmt.accept(self)

        node.return_node.accept(self)

        return self.__build_final_output()

    def __reset_state(self):
        self.translated_lines = []
        self.struct_type_lines = []
        self.function_definitions = []

    def __build_final_output(self) -> str:
        result = [self.get_print_function_llvm()]

        if self.struct_type_lines:
            result.extend(self.struct_type_lines)
            result.append("")

        if self.function_definitions:
            result.extend(self.function_definitions)
            result.append("")

        result.append("define i32 @main() {")
        result.extend(self.translated_lines)
        result.append("}")

        return "\n".join(result)

    def visit_struct_declaration(self, node: StructDeclNode):
        fields = self.__build_struct_fields(node)
        self.struct_definitions[node.variable] = fields

        field_types = [f[1] for f in fields]
        struct_def = f"%struct.{node.variable} = type {{ {', '.join(field_types)} }}"
        self.struct_type_lines.append(struct_def)

    def __build_struct_fields(self, node: StructDeclNode) -> list:
        fields = []
        for field in node.fields:
            llvm_type = self.__get_llvm_type(field.data_type)
            fields.append((field.variable, llvm_type, field.data_type))
        return fields

    @staticmethod
    def __get_llvm_type(type_name: str) -> str:
        if DataType.is_data_type(type_name):
            return DataType.from_string(type_name).to_llvm()
        return f"%struct.{type_name}"

    def visit_struct_initialization(self, node: StructInitNode):
        struct_reg = self.__allocate_struct(node.struct_type)
        self.__initialize_struct_fields(node, struct_reg)
        return struct_reg

    def __allocate_struct(self, struct_name: str) -> str:
        struct_reg = self.__get_temp_register()
        self.translated_lines.append(f"  {struct_reg} = alloca %struct.{struct_name}")
        return struct_reg

    def __initialize_struct_fields(self, node: StructInitNode, struct_reg: str):
        fields = self.struct_definitions[node.struct_type]

        for i, (field_name, field_llvm_type, field_data_type) in enumerate(fields):
            expr_value = node.init_expressions[i].accept(self)
            expr_value = self.__convert_type_if_needed(
                expr_value,
                self.__get_node_type(node.init_expressions[i]),
                field_data_type
            )

            field_ptr = self.__get_struct_field_ptr(node.struct_type, struct_reg, i)
            self.translated_lines.append(f"  store {field_llvm_type} {expr_value}, {field_llvm_type}* {field_ptr}")

    def __get_struct_field_ptr(self, struct_name: str, struct_ptr: str, field_index: int) -> str:
        field_ptr = self.__get_temp_register()
        self.translated_lines.append(f"  {field_ptr} = getelementptr inbounds %struct.{struct_name}, "
                                     f"%struct.{struct_name}* {struct_ptr}, i32 0, i32 {field_index}")
        return field_ptr

    def __convert_type_if_needed(self, value: str, expr_type, target_type: str) -> str:
        if isinstance(expr_type, DataType) and DataType.is_data_type(target_type):
            target_datatype = DataType.from_string(target_type)
            if expr_type == DataType.I32 and target_datatype == DataType.I64:
                return self.__widen_to_i64(value)
        return value

    def __widen_to_i64(self, value: str) -> str:
        temp_reg = self.__get_temp_register()
        self.translated_lines.append(f"  {temp_reg} = sext i32 {value} to i64")
        return temp_reg

    def visit_struct_field(self, node: StructFieldNode):
        current_reg = self.__get_current_register(node.field_chain[0])
        current_type = self.variable_types[node.field_chain[0]]

        for i in range(1, len(node.field_chain)):
            current_reg, current_type = self.__access_field(
                node.field_chain[i],
                current_type,
                current_reg,
                is_final=(i == len(node.field_chain) - 1))

        return current_reg

    def __access_field(self, field_name: str, current_type, current_reg: str, is_final: bool):
        if not isinstance(current_type, str):
            return current_reg, current_type

        struct_name = current_type
        fields = self.struct_definitions[struct_name]
        field_index, field_llvm_type, field_data_type = self.__find_field(fields, field_name)

        field_ptr = self.__get_struct_field_ptr(struct_name, current_reg, field_index)

        if is_final:
            value_reg = self.__get_temp_register()
            self.translated_lines.append(f"  {value_reg} = load {field_llvm_type}, {field_llvm_type}* {field_ptr}")
            current_reg = value_reg
        else:
            current_reg = field_ptr

        new_type = DataType.from_string(field_data_type) if DataType.is_data_type(field_data_type) else field_data_type
        return current_reg, new_type

    @staticmethod
    def __find_field(fields: list, field_name: str) -> tuple:
        for i, (name, field_type, fdata) in enumerate(fields):
            if name == field_name:
                return i, field_type, fdata
        raise ValueError(f"Field {field_name} not found")

    def visit_struct_field_assignment(self, node: StructFieldAssignNode):
        current_reg = self.__get_current_register(node.target.field_chain[0])
        current_type = self.variable_types[node.target.field_chain[0]]

        for i in range(1, len(node.target.field_chain)):
            is_final = (i == len(node.target.field_chain) - 1)

            if isinstance(current_type, str):
                struct_name = current_type
                fields = self.struct_definitions[struct_name]
                field_index, field_llvm_type, field_data_type = self.__find_field(fields, node.target.field_chain[i])

                field_ptr = self.__get_struct_field_ptr(struct_name, current_reg, field_index)

                if is_final:
                    expr_value = node.expr_node.accept(self)
                    expr_value = self.__convert_type_if_needed(expr_value, self.__get_node_type(node.expr_node),
                                                               field_data_type)
                    self.translated_lines.append(
                        f"  store {field_llvm_type} {expr_value}, {field_llvm_type}* {field_ptr}")
                else:
                    current_reg = field_ptr
                    current_type = DataType.from_string(field_data_type) if DataType.is_data_type(
                        field_data_type) else field_data_type

    def visit_function_declaration(self, node: FunctionDeclNode):
        saved_state = self.__save_state()
        self.__reset_function_state()

        func_signature = self.__build_function_signature(node)
        self.__declare_function_params(node)

        node.body.accept(self)

        self.__store_function_definition(func_signature)
        self.__restore_state(saved_state)

    def __save_state(self) -> dict:
        return {
            'lines': self.translated_lines,
            'versions': self.variable_versions.copy(),
            'types': self.variable_types.copy(),
            'temp': self.temp_counter,
            'label': self.label_counter
        }

    def __restore_state(self, state: dict):
        self.translated_lines = state['lines']
        self.variable_versions = state['versions']
        self.variable_types = state['types']
        self.temp_counter = state['temp']
        self.label_counter = state['label']
        self.in_function = False

    def __reset_function_state(self):
        self.translated_lines = []
        self.variable_versions = {}
        self.variable_types = {}
        self.temp_counter = 0
        self.label_counter = 0
        self.in_function = True

    def __build_function_signature(self, node: FunctionDeclNode) -> str:
        param_strs = [self.__build_param_string(p) for p in node.params]
        return_llvm_type = self.__get_llvm_type(node.return_type)
        return f"define {return_llvm_type} @{node.variable}({', '.join(param_strs)}) {{"

    def __build_param_string(self, param) -> str:
        param_llvm_type = self.__get_llvm_type(param.param_type)
        return f"{param_llvm_type} %{param.name}"

    def __declare_function_params(self, node: FunctionDeclNode):
        for param in node.params:
            if DataType.is_data_type(param.param_type):
                self.variable_types[param.name] = DataType.from_string(param.param_type)
            else:
                self.variable_types[param.name] = param.param_type
            self.variable_versions[param.name] = 0

    def __store_function_definition(self, signature: str):
        self.function_definitions.append(signature)
        self.function_definitions.extend(self.translated_lines)
        self.function_definitions.append("}")
        self.function_definitions.append("")

    def visit_function_call(self, node: FunctionCallNode):
        args = [self.__build_call_argument(arg) for arg in node.arguments]
        result_reg = self.__get_temp_register()
        self.translated_lines.append(f"  {result_reg} = call ? @{node.value}({', '.join(args)})")
        return result_reg

    def __build_call_argument(self, arg) -> str:
        arg_value = arg.accept(self)
        arg_type = self.__get_node_type(arg)

        if isinstance(arg_type, DataType):
            arg_llvm_type = arg_type.to_llvm()
        else:
            arg_llvm_type = f"%struct.{arg_type}*"

        return f"{arg_llvm_type} {arg_value}"

    def visit_declaration(self, node):
        if isinstance(node.data_type, str):
            self.__declare_struct_variable(node)
        else:
            self.__declare_primitive_variable(node)

    def __declare_struct_variable(self, node):
        struct_value = node.expr_node.accept(self)
        reg = self.__get_variable_register(node.variable)
        self.variable_types[node.variable] = node.data_type

        self.translated_lines.append(f"  {reg} = alloca %struct.{node.data_type}")
        self.__copy_struct_fields(node.data_type, struct_value, reg)

    def __copy_struct_fields(self, struct_name: str, src_ptr: str, dst_ptr: str):
        fields = self.struct_definitions[struct_name]
        for i, (field_name, field_llvm_type, _) in enumerate(fields):
            src_field_ptr = self.__get_struct_field_ptr(struct_name, src_ptr, i)
            src_val = self.__load_value(field_llvm_type, src_field_ptr)

            dst_field_ptr = self.__get_struct_field_ptr(struct_name, dst_ptr, i)
            self.translated_lines.append(f"  store {field_llvm_type} {src_val}, {field_llvm_type}* {dst_field_ptr}")

    def __load_value(self, llvm_type: str, ptr: str) -> str:
        val_reg = self.__get_temp_register()
        self.translated_lines.append(f"  {val_reg} = load {llvm_type}, {llvm_type}* {ptr}")
        return val_reg

    def __declare_primitive_variable(self, node):
        llvm_type = node.data_type.to_llvm()
        value = node.expr_node.accept(self)
        reg = self.__get_variable_register(node.variable)

        self.variable_types[node.variable] = node.data_type

        expr_type = self.__get_node_type(node.expr_node)
        if expr_type == DataType.I32 and node.data_type == DataType.I64:
            value = self.__widen_to_i64(value)

        self.translated_lines.append(f"  {reg} = add {llvm_type} 0, {value}")

    def visit_assignment(self, node):
        var_type = self.variable_types[node.variable]

        if not isinstance(var_type, DataType):
            raise ValueError(
                f"Cannot reassign entire struct variable '{node.variable}' at line {node.line}! "
                f"Use field assignment instead: {node.variable}.field = value")

        llvm_type = var_type.to_llvm()
        value = node.expr_node.accept(self)
        reg = self.__get_variable_register(node.variable)

        expr_type = self.__get_node_type(node.expr_node)
        if expr_type == DataType.I32 and var_type == DataType.I64:
            value = self.__widen_to_i64(value)

        self.translated_lines.append(f"  {reg} = add {llvm_type} 0, {value}")

    def visit_return(self, node):
        value = node.expr_node.accept(self)
        return_type = self.__get_node_type(node.expr_node)

        if self.in_function:
            self.__generate_function_return(value, return_type)
        else:
            self.__generate_main_return(value, return_type)

    def __generate_function_return(self, value: str, return_type):
        llvm_type = self.__get_llvm_type(return_type) if isinstance(return_type, str) else return_type.to_llvm()
        self.translated_lines.append(f"  ret {llvm_type} {value}")

    def __generate_main_return(self, value: str, return_type):
        if not isinstance(return_type, DataType):
            raise NotImplementedError(
                f"Cannot return struct types from main. Attempted to return value of type '{return_type}'")

        value = self.__cast_to_i32(value, return_type)
        self.translated_lines.append(f"  call void @printResult(i32 {value})")
        self.translated_lines.append(f"  ret i32 {value}")

    def __cast_to_i32(self, value: str, value_type: DataType) -> str:
        if value_type == DataType.BOOL:
            cast_reg = self.__get_temp_register()
            self.translated_lines.append(f"  {cast_reg} = zext i1 {value} to i32")
            return cast_reg
        elif value_type == DataType.I64:
            cast_reg = self.__get_temp_register()
            self.translated_lines.append(f"  {cast_reg} = trunc i64 {value} to i32")
            return cast_reg
        return value

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
        self.translated_lines.append(f"  {temp_reg} = {llvm_op} {operand_type} {left_value}, {right_value}")

    def __generate_arithmetic(self, node, left_value, right_value, left_type, right_type, temp_reg):
        result_type = node.result_type if node.result_type else DataType.I32
        llvm_type = result_type.to_llvm()

        if result_type == DataType.I64:
            left_value = self.__widen_if_needed(left_value, left_type, "i64")
            right_value = self.__widen_if_needed(right_value, right_type, "i64")

        llvm_op = node.operator.to_llvm()
        self.translated_lines.append(f"  {temp_reg} = {llvm_op} {llvm_type} {left_value}, {right_value}")

    def __widen_if_needed(self, value, current_type, target_type):
        if target_type == "i64" and current_type == DataType.I32:
            return self.__widen_to_i64(value)
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

    def __get_node_type(self, node):
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
        if isinstance(node, StructInitNode):
            return node.struct_type
        if isinstance(node, StructFieldNode):
            return self.__get_struct_field_type(node)
        if isinstance(node, FunctionCallNode):
            return DataType.I32
        return DataType.I32

    def __get_struct_field_type(self, node: StructFieldNode):
        current_type = self.variable_types[node.field_chain[0]]

        for i in range(1, len(node.field_chain)):
            if isinstance(current_type, str):
                fields = self.struct_definitions[current_type]
                field_info = next((f for f in fields if f[0] == node.field_chain[i]), None)
                if field_info:
                    field_data_type = field_info[2]
                    current_type = DataType.from_string(field_data_type) if DataType.is_data_type(
                        field_data_type) else field_data_type

        return current_type

    def visit_if_statement(self, node: IfNode):
        label_id = self.__get_next_label_id()
        then_label, else_label, end_label = self.__generate_if_labels(label_id, node.else_block is not None)

        condition_value = node.condition.accept(self)
        self.translated_lines.append(f"  br i1 {condition_value}, label %{then_label}, label %{else_label}")

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
        saved_versions = self.variable_versions.copy()
        saved_types = self.variable_types.copy()

        for n in node.statements:
            n.accept(self)
        if node.return_node:
            node.return_node.accept(self)

        self.variable_versions = saved_versions
        self.variable_types = saved_types

    def visit_unary_operation(self, node: UnaryOpNode):
        if node.operator == NOT:
            operand = node.operand.accept(self)
            temp_reg = self.__get_temp_register()
            self.translated_lines.append(f"  {temp_reg} = xor i1 {operand}, 1")
            return temp_reg

        raise ValueError(f"We do not support this unary operator: {node.operator}")
