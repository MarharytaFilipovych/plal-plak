#!/usr/bin/env python3
from ...llvm_specifics.data_type import DataType
from ...node.struct_decl_node import StructDeclNode
from ...node.struct_init_node import StructInitNode
from ...node.struct_field_node import StructFieldNode
from ...node.struct_field_assign_node import StructFieldAssignNode


class StructAnalyzer:
    def __init__(self, context, parent_visitor):
        self.context = context
        self.parent = parent_visitor

    def visit_struct_declaration(self, node: StructDeclNode):
        self._check_duplicate_fields(node)
        self._validate_field_types(node)
        self.context.define_struct(node.variable, node.fields)
        self._register_member_functions(node.variable, node.member_functions)
        [self._analyze_member_function(node.variable, member_func) for member_func in node.member_functions]

    def visit_struct_initialization(self, node: StructInitNode) -> str:
        if not self.context.is_struct_defined(node.struct_type):
            raise ValueError(f"No such struct type '{node.struct_type}' at line {node.line}!")

        struct_fields = self.context.get_struct_definition(node.struct_type)
        self._validate_field_count(node, struct_fields)
        self._validate_field_types_in_init(node, struct_fields)

        return node.struct_type

    def visit_struct_field(self, node: StructFieldNode):
        if not self.context.is_variable_declared(node.value):
            raise ValueError(f"Variable '{node.value}' not declared at line {node.line}!")

        current_type = self.context.get_variable_type(node.value)
        base_mutable = self.context.is_variable_mutable(node.value)

        for i in range(1, len(node.field_chain.fields)):
            current_type, base_mutable = self._traverse_field_chain(
                node.field_chain.fields[i], current_type, base_mutable, node.line)

        node.is_mutable = base_mutable
        return current_type

    def visit_struct_field_assignment(self, node: StructFieldAssignNode):
        field_type = node.target.accept(self.parent)

        if not node.target.is_mutable:
            raise ValueError(f"Cannot assign to immutable field '{node.target.field_chain}' at line {node.line}! "
                             f"Either the base object or a field in the chain is not mutable.")

        expr_type = node.expr_node.accept(self.parent)
        if not self._types_match(expr_type, field_type):
            raise ValueError(f"Types do not match at line {node.line}: "
                             f"you cannot assign {expr_type} to {field_type}! Be careful!")

    def _register_member_functions(self, struct_name: str, member_functions):
        member_func_names = set()
        for member_function in member_functions:
            if member_function.variable in member_func_names:
                raise ValueError(f"Duplicate member function '{member_function.variable}' "
                                 f"in struct '{struct_name}' at line {member_function.line}! "
                                 "Don't you have enough imagination to create sth new???")
            member_func_names.add(member_function.variable)

            param_types = [p.param_type for p in member_function.params]
            self.context.define_function(struct_name, member_function.variable,
                                         param_types, member_function.return_type)

    @staticmethod
    def _check_duplicate_fields(node: StructDeclNode):
        field_names = set()
        for field in node.fields:
            if field.variable in field_names:
                raise ValueError(f"Duplicate field name '{field.variable}' in struct '{node.variable}' "
                                 f"at line {node.line}! GET RID OF IT!")
            field_names.add(field.variable)

    def _validate_field_types(self, node: StructDeclNode):
        for field in node.fields:
            if not self._is_valid_type(field.data_type):
                raise ValueError(f"The type '{field.data_type}' for field '{field.variable}' "
                                 f"in struct '{node.variable}' at line {node.line} does not exist!")

    def _is_valid_type(self, type_name: str) -> bool:
        return DataType.is_data_type(type_name) or self.context.is_struct_defined(type_name)

    @staticmethod
    def _validate_field_count(node: StructInitNode, struct_fields):
        if len(node.init_expressions) != len(struct_fields):
            raise ValueError(f"Struct '{node.struct_type}' expects {len(struct_fields)} fields "
                             f"but you typed {len(node.init_expressions)} at line {node.line}!")

    def _validate_field_types_in_init(self, node: StructInitNode, struct_fields):
        for i, field in enumerate(struct_fields):
            expr_type = node.init_expressions[i].accept(self.parent)
            expected_type = self._resolve_type(field.data_type)

            if not self._types_match(expr_type, expected_type):
                raise ValueError(f"Type mismatch for field '{field.variable}' in struct '{node.struct_type}': "
                                 f"expected {expected_type}, but you typed {expr_type} at line {node.line}!")

    def _traverse_field_chain(self, field_name: str, current_type, base_mutable: bool, line: int):
        if isinstance(current_type, DataType):
            raise ValueError(f"Cannot access field '{field_name}' on primitive type '{current_type}' at line {line}!")

        if not self.context.is_struct_defined(current_type):
            raise ValueError(
                f"Type '{current_type}' is not a defined struct, cannot access field '{field_name}' at line {line}!")

        struct_fields = self.context.get_struct_definition(current_type)
        field_info = next((field for field in struct_fields if field.variable == field_name), None)

        if not field_info:
            raise ValueError(f"Struct '{current_type}' has no field '{field_name}' at line {line}!")

        new_mutable = base_mutable and field_info.mutable
        new_type = self._resolve_type(field_info.data_type)

        return new_type, new_mutable

    def _analyze_member_function(self, struct_name: str, node):
        self.context.enter_scope()
        self.parent._current_struct_context = struct_name

        struct_fields = self.context.get_struct_definition(struct_name)
        for field in struct_fields:
            field_type = self._resolve_type(field.data_type)
            self.context.declare_variable(field.variable, field_type, field.mutable)

        self._declare_function_parameters(node)

        if not node.body.return_node:
            raise ValueError(
                f"Member function '{node.variable}' in struct '{struct_name}' must have a return statement!")

        self.parent._expected_return_type = self._resolve_type(node.return_type)
        self.parent._function_name = f"{struct_name}::{node.variable}"

        node.body.accept(self.parent)

        self.parent._expected_return_type = None
        self.parent._function_name = None
        self.parent._current_struct_context = None
        self.context.exit_scope()

    def _declare_function_parameters(self, node):
        for param in node.params:
            param_type = self._resolve_type(param.param_type)
            if not self.context.declare_variable(param.name, param_type, mutable=False):
                raise ValueError(f"Duplicate parameter '{param.name}' in function '{node.variable}'!")

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