#!/usr/bin/env python3
from ...llvm_specifics.boolean import Boolean
from ...llvm_specifics.data_type import DataType
from ..ast_visitor import ASTVisitor
from ...node.code_block_node import CodeBlockNode
from ...node.if_node import IfNode
from ...constants import NOT
from .variable_registry import VariableRegistry
from .llvm_emitter import LLVMEmitter
from .type_converter import TypeConverter
from .struct_operations import StructOperations
from .function_generator import FunctionGenerator


class CodeGenerator(ASTVisitor):

    def __init__(self):
        self.variable_registry = VariableRegistry()
        self.emitter = LLVMEmitter()
        self.type_converter = None
        self.struct_ops = None
        self.func_gen = None
        self._initialize_helpers()

    def _initialize_helpers(self):
        self.type_converter = TypeConverter(self.variable_registry, None, {})
        self.struct_ops = StructOperations(self.emitter, self.variable_registry, self.type_converter)
        self.func_gen = FunctionGenerator(self.emitter, self.variable_registry,
                                          self.type_converter, self.struct_ops)
        self.type_converter.struct_ops = self.struct_ops
        self.type_converter.function_return_types = self.func_gen.function_return_types

    def visit_program(self, node):
        self._reset_state()
        [decl.accept(self) for decl in node.struct_decls + node.func_decls + node.statement_nodes]
        node.return_node.accept(self)
        return self.emitter.build_final_output()

    def _reset_state(self):
        self.emitter.translated_lines = []
        self.emitter.struct_type_lines = []
        self.emitter.function_definitions = []

    def visit_struct_declaration(self, node):
        fields = self.struct_ops.build_struct_fields(node)
        self.struct_ops.register_struct(node.variable, fields)
        [self.func_gen.generate_member_function(node.variable, member_func, self)
         for member_func in node.member_functions]

    def visit_struct_initialization(self, node):
        struct_reg = self.struct_ops.allocate_struct(node.struct_type)
        self.struct_ops.initialize_struct_fields(node, struct_reg, self)
        return struct_reg

    def visit_struct_field(self, node):
        current_reg = self.variable_registry.get_current_register(node.field_chain.fields[0])
        current_type = self.variable_registry.get_variable_type(node.field_chain.fields[0])

        for i in range(1, len(node.field_chain.fields)):
            current_reg, current_type = self.struct_ops.access_field(
                node.field_chain.fields[i],
                current_type,
                current_reg,
                is_final=(i == len(node.field_chain.fields) - 1))

        return current_reg

    def visit_struct_field_assignment(self, node):
        base_field = node.target.field_chain.fields[0]
        current_reg = self.variable_registry.get_current_register(base_field)
        current_type = self.variable_registry.get_variable_type(base_field)

        for i in range(1, len(node.target.field_chain.fields)):
            field_name = node.target.field_chain.fields[i]
            is_final = (i == len(node.target.field_chain.fields) - 1)

            current_reg, current_type = self.__prepare_field_assignment(
                current_reg, current_type, field_name, node, is_final)

    def __prepare_field_assignment(self, current_reg, current_type, field_name, node, is_final):
        if not isinstance(current_type, str):
            return current_reg, current_type

        struct_name = current_type
        fields = self.struct_ops.struct_definitions[struct_name]
        field_index, field_llvm_type, field_data_type = self.struct_ops.find_field(fields, field_name)
        field_ptr = self.struct_ops.get_struct_field_ptr(struct_name, current_reg, field_index)

        if is_final:
            self.__store_final_field_value(node, field_ptr, field_llvm_type, field_data_type)
        else:
            current_reg = field_ptr
            current_type = (DataType.from_string(field_data_type)
                            if DataType.is_data_type(field_data_type)
                            else field_data_type)

        return current_reg, current_type

    def __store_final_field_value(self, node, field_ptr, field_llvm_type, field_data_type):
        expr_value = node.expr_node.accept(self)
        expr_type = self.type_converter.get_node_type(node.expr_node)

        expr_value = self.struct_ops.convert_type_if_needed(expr_value, expr_type, field_data_type)
        self.emitter.emit_line(f"  store {field_llvm_type} {expr_value}, {field_llvm_type}* {field_ptr}")

    def visit_function_declaration(self, node):
        self.func_gen.generate_standalone_function(node, self)

    def visit_function_call(self, node):
        return (self.func_gen.generate_member_function_call(node, self)
                if node.field_chain
                else self.func_gen.generate_regular_function_call(node, self))

    def visit_declaration(self, node):
        (self.__declare_struct_variable(node)
         if isinstance(node.data_type, str)
         else self.__declare_primitive_variable(node))

    def __declare_struct_variable(self, node):
        struct_value = node.expr_node.accept(self)
        reg = self.variable_registry.get_variable_register(node.variable)
        self.variable_registry.set_variable_type(node.variable, node.data_type)

        self.emitter.emit_line(f"  {reg} = alloca %struct.{node.data_type}")
        self.struct_ops.copy_struct_fields(node.data_type, struct_value, reg)

    def __declare_primitive_variable(self, node):
        llvm_type = node.data_type.to_llvm()
        value = node.expr_node.accept(self)
        reg = self.variable_registry.get_variable_register(node.variable)

        self.variable_registry.set_variable_type(node.variable, node.data_type)

        expr_type = self.type_converter.get_node_type(node.expr_node)
        if expr_type == DataType.I32 and node.data_type == DataType.I64:
            value = self.struct_ops.widen_to_i64(value)

        self.emitter.emit_line(f"  {reg} = add {llvm_type} 0, {value}")

    def visit_assignment(self, node):
        if self.variable_registry.is_field_access_from_this(node.variable):
            expr_value = node.expr_node.accept(self)
            self.func_gen.store_field_to_this(node.variable, expr_value)
            return
        var_type = self.__validate_assignable_variable(node)
        self.__emit_assignment_code(node, var_type)

    def __validate_assignable_variable(self, node):
        var_type = self.variable_registry.get_variable_type(node.variable)
        if not isinstance(var_type, DataType):
            raise ValueError(f"Cannot reassign entire struct variable '{node.variable}' at line {node.line}! "
                             f"Use field assignment instead: {node.variable}.field = value")
        return var_type

    def __emit_assignment_code(self, node, var_type):
        llvm_type = var_type.to_llvm()
        value = node.expr_node.accept(self)
        reg = self.variable_registry.get_variable_register(node.variable)

        expr_type = self.type_converter.get_node_type(node.expr_node)
        if expr_type == DataType.I32 and var_type == DataType.I64:
            value = self.struct_ops.widen_to_i64(value)

        self.emitter.emit_line(f"  {reg} = add {llvm_type} 0, {value}")

    def visit_return(self, node):
        value = node.expr_node.accept(self)
        return_type = self.type_converter.get_node_type(node.expr_node)
        self.__generate_function_return(value, return_type) \
            if self.func_gen.in_function else self._generate_main_return(value, return_type)

    def __generate_function_return(self, value: str, return_type):
        llvm_type = (self.type_converter.get_llvm_type(return_type)
                     if isinstance(return_type, str)
                     else return_type.to_llvm())
        self.emitter.emit_line(f"  ret {llvm_type} {value}")

    def _generate_main_return(self, value: str, return_type):
        if not isinstance(return_type, DataType):
            raise NotImplementedError(f"Cannot return struct types from main. "
                                      f"Attempted to return value of type '{return_type}'")

        value = self.__cast_to_i32(value, return_type)
        self.emitter.emit_line(f"  call void @printResult(i32 {value})")
        self.emitter.emit_line(f"  ret i32 {value}")

    def __cast_to_i32(self, value: str, value_type: DataType) -> str:
        if value_type == DataType.BOOL:
            cast_reg = self.emitter.get_temp_register()
            self.emitter.emit_line(f"  {cast_reg} = zext i1 {value} to i32")
            return cast_reg
        elif value_type == DataType.I64:
            cast_reg = self.emitter.get_temp_register()
            self.emitter.emit_line(f"  {cast_reg} = trunc i64 {value} to i32")
            return cast_reg
        return value

    def visit_binary_operation(self, node):
        left_value = node.left.accept(self)
        right_value = node.right.accept(self)

        left_type = self.type_converter.get_node_type(node.left)
        right_type = self.type_converter.get_node_type(node.right)

        temp_reg = self.emitter.get_temp_register()

        (self.__generate_comparison(node, left_value, right_value, left_type, right_type, temp_reg)
         if node.operator.is_for_comparison()
         else self.__generate_arithmetic(node, left_value, right_value, left_type, right_type, temp_reg))

        return temp_reg

    def __generate_comparison(self, node, left_value, right_value, left_type, right_type, temp_reg):
        operand_type = self.type_converter.infer_operand_type(node.left, node.right)

        left_value = self.__widen_if_needed(left_value, left_type, operand_type)
        right_value = self.__widen_if_needed(right_value, right_type, operand_type)

        llvm_op = node.operator.to_llvm()
        self.emitter.emit_line(f"  {temp_reg} = {llvm_op} {operand_type} {left_value}, {right_value}")

    def __generate_arithmetic(self, node, left_value, right_value, left_type, right_type, temp_reg):
        result_type = node.result_type if node.result_type else DataType.I32
        llvm_type = result_type.to_llvm()

        if result_type == DataType.I64:
            left_value = self.__widen_if_needed(left_value, left_type, "i64")
            right_value = self.__widen_if_needed(right_value, right_type, "i64")

        llvm_op = node.operator.to_llvm()
        self.emitter.emit_line(f"  {temp_reg} = {llvm_op} {llvm_type} {left_value}, {right_value}")

    def __widen_if_needed(self, value, current_type, target_type):
        if target_type == "i64" and current_type == DataType.I32:
            return self.struct_ops.widen_to_i64(value)
        return value

    def visit_id(self, node):
        return (self.func_gen.load_field_from_this(node.value)
                if self.variable_registry.is_field_access_from_this(node.value)
                else self.variable_registry.get_current_register(node.value))

    def visit_number(self, node):
        return node.value

    def visit_boolean(self, node):
        return Boolean.from_string(node.value).to_llvm()

    def visit_if_statement(self, node: IfNode):
        label_id = self.emitter.get_next_label_id()
        then_label, else_label, end_label = self.__generate_if_labels(label_id, node.else_block is not None)

        condition_value = node.condition.accept(self)
        self.emitter.emit_line(f"  br i1 {condition_value}, label %{then_label}, label %{else_label}")

        self.__emit_block_with_label(node.then_block, then_label, end_label)

        if node.else_block:
            self.__emit_block_with_label(node.else_block, else_label, end_label)

        self.emitter.emit_label(end_label)

    @staticmethod
    def __generate_if_labels(label_id: int, has_else: bool) -> tuple[str, str, str]:
        then_label = f"then_{label_id}"
        else_label = f"else_{label_id}" if has_else else f"end_{label_id}"
        end_label = f"end_{label_id}"
        return then_label, else_label, end_label

    def __emit_block_with_label(self, block: CodeBlockNode, label: str, end_label: str):
        self.emitter.emit_label(label)
        block.accept(self)
        if not block.return_node:
            self.emitter.emit_line(f"  br label %{end_label}")

    def visit_code_block(self, node: CodeBlockNode):
        saved_state = self.variable_registry.copy_state()
        [n.accept(self) for n in node.statements]
        if node.return_node:
            node.return_node.accept(self)
        self.variable_registry.restore_state(saved_state)

    def visit_unary_operation(self, node):
        if node.operator == NOT:
            operand = node.operand.accept(self)
            temp_reg = self.emitter.get_temp_register()
            self.emitter.emit_line(f"  {temp_reg} = xor i1 {operand}, 1")
            return temp_reg
        raise ValueError(f"We do not support this unary operator: {node.operator}")