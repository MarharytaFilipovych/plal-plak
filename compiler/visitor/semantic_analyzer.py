#!/usr/bin/env python3
from ..constants import I32_MAX, I32_MIN
from .ast_visitor import ASTVisitor
from compiler.context.context import Context
from ..llvm_specifics.data_type import DataType
from ..node.assign_node import AssignNode
from ..node.binary_op_node import BinaryOpNode
from ..node.bool_node import BooleanNode
from ..node.code_block_node import CodeBlockNode
from ..node.decl_node import DeclNode
from ..node.function_call_node import FunctionCallNode
from ..node.function_decl_node import FunctionDeclNode
from ..node.id_node import IDNode
from ..node.number_node import NumberNode
from ..node.program_node import ProgramNode
from ..node.return_node import ReturnNode
from ..node.struct_field_assign_node import StructFieldAssignNode
from ..node.struct_field_node import StructFieldNode
from ..node.unary_op_node import UnaryOpNode
from ..node.struct_decl_node import StructDeclNode
from ..node.struct_init_node import StructInitNode


class SemanticAnalyzer(ASTVisitor):
    def __init__(self):
        self.context = Context()

    def visit_program(self, node: ProgramNode):
        for struct_decl in node.struct_decls:
            struct_decl.accept(self)

        for func_decl in node.func_decls:
            self.__register_function(func_decl)

        for func_decl in node.func_decls:
            func_decl.accept(self)

        for stmt in node.statement_nodes:
            stmt.accept(self)

        node.return_node.accept(self)

    def visit_struct_declaration(self, node: StructDeclNode):
        self.__check_duplicate_fields(node)
        self.__validate_field_types(node)
        self.context.define_struct(node.variable, node.fields)

    @staticmethod
    def __check_duplicate_fields(node: StructDeclNode):
        field_names = set()
        for field in node.fields:
            if field.variable in field_names:
                raise ValueError(f"Duplicate field name '{field.variable}' in struct '{node.variable}' "
                                 f"at line {node.line}! GET RID OF IT!")
            field_names.add(field.variable)

    def __validate_field_types(self, node: StructDeclNode):
        for field in node.fields:
            if not self.__is_valid_type(field.data_type):
                raise ValueError(f"The type '{field.data_type}' for field '{field.variable}' "
                                 f"in struct '{node.variable}' at line {node.line} does not exist!")

    def __is_valid_type(self, type_name: str) -> bool:
        return DataType.is_data_type(type_name) or self.context.is_struct_defined(type_name)

    def visit_struct_initialization(self, node: StructInitNode) -> str:
        if not self.context.is_struct_defined(node.struct_type):
            raise ValueError(f"No such struct type '{node.struct_type}' at line {node.line}!")

        struct_fields = self.context.get_struct_definition(node.struct_type)
        self.__validate_field_count(node, struct_fields)
        self.__validate_field_types_in_init(node, struct_fields)

        return node.struct_type

    @staticmethod
    def __validate_field_count(node: StructInitNode, struct_fields):
        if len(node.init_expressions) != len(struct_fields):
            raise ValueError(f"Struct '{node.struct_type}' expects {len(struct_fields)} fields "
                             f"but you typed {len(node.init_expressions)} at line {node.line}!")

    def __validate_field_types_in_init(self, node: StructInitNode, struct_fields):
        for i, field in enumerate(struct_fields):
            expr_type = node.init_expressions[i].accept(self)
            expected_type = self.__resolve_type(field.data_type)

            if not self.__types_match(expr_type, expected_type):
                raise ValueError(f"Type mismatch for field '{field.variable}' in struct '{node.struct_type}': "
                                 f"expected {expected_type}, but you typed {expr_type} at line {node.line}!")

    @staticmethod
    def __resolve_type(type_str: str):
        return DataType.from_string(type_str) if DataType.is_data_type(type_str) else type_str

    def visit_struct_field(self, node: StructFieldNode):
        self.__check_variable_declared(node.value, node.line)

        current_type = self.context.get_variable_type(node.value)
        base_mutable = self.context.is_variable_mutable(node.value)

        for i in range(1, len(node.field_chain)):
            current_type, base_mutable = self.__traverse_field_chain(
                node.field_chain[i], current_type, base_mutable, node.line)

        node.is_mutable = base_mutable
        return current_type

    def __traverse_field_chain(self, field_name: str, current_type, base_mutable: bool, line: int):
        if isinstance(current_type, DataType):
            raise ValueError(f"Cannot access field '{field_name}' on primitive type '{current_type}' at line {line}!")

        if not self.context.is_struct_defined(current_type):
            raise ValueError(f"Type '{current_type}' is not a defined struct, cannot access field '{field_name}' at line {line}!")

        struct_fields = self.context.get_struct_definition(current_type)
        field_info = next((field for field in struct_fields if field.variable == field_name), None)

        if not field_info:
            raise ValueError(f"Struct '{current_type}' has no field '{field_name}' at line {line}!")

        new_mutable = base_mutable and field_info.mutable
        new_type = self.__resolve_type(field_info.data_type)

        return new_type, new_mutable

    def visit_struct_field_assignment(self, node: StructFieldAssignNode):
        field_type = node.target.accept(self)

        if not node.target.is_mutable:
            field_path = '.'.join(node.target.field_chain)
            raise ValueError(f"Cannot assign to immutable field '{field_path}' at line {node.line}! "
                             f"Either the base object or a field in the chain is not mutable.")

        expr_type = node.expr_node.accept(self)
        self.__check_type_match(expr_type, field_type, node.line)

    def visit_declaration(self, node: DeclNode):
        if isinstance(node.data_type, str):
            self.__validate_struct_type_exists(node.data_type, node.line)

        if not self.context.declare_variable(node.variable, node.data_type, node.mutable):
            raise ValueError(f"Variable '{node.variable}' has already been declared at line {node.line}!!!!!!!!!!")

        self.context.currently_initializing = node.variable
        expr_type = node.expr_node.accept(self)
        self.__check_type_match(expr_type, node.data_type, node.line)
        self.context.currently_initializing = None

    def __validate_struct_type_exists(self, type_name: str, line: int):
        if not self.context.is_struct_defined(type_name):
            raise ValueError(f"Type '{type_name}' is not defined at line {line}! "
                             f"Did you forget to declare the struct?")

    def __check_variable_declared(self, var_name: str, line: int):
        if not self.context.is_variable_declared(var_name):
            raise ValueError(f"Variable '{var_name}' not declared at line {line}!")

    def __check_variable_mutable(self, var_name: str, line: int):
        if not self.context.is_variable_mutable(var_name):
            raise ValueError(f"Sorry, but you cannot assign something new to an immutable variable!!! "
                             f"Remove '{var_name}' from line {line}!")

    def __check_type_match(self, expr_type, expected_type, line: int):
        if not self.__types_match(expr_type, expected_type):
            raise ValueError(f"Types do not match at line {line}: "
                             f"you cannot assign {expr_type} to {expected_type}! Be careful!")

    def visit_assignment(self, node: AssignNode):
        self.__check_variable_declared(node.variable, node.line)
        self.__check_variable_mutable(node.variable, node.line)

        if isinstance(node.expr_node, IDNode) and node.expr_node.value == node.variable:
            raise ValueError(
                f"Self-assignment like '{node.variable} = {node.variable}' is not allowed at line {node.line}!")

        data_type = self.context.get_variable_type(node.variable)
        expr_type = node.expr_node.accept(self)
        self.__check_type_match(expr_type, data_type, node.line)

    def visit_return(self, node: ReturnNode):
        return node.expr_node.accept(self)

    def visit_binary_operation(self, node: BinaryOpNode):
        left_type = node.left.accept(self)
        right_type = node.right.accept(self)

        self.__validate_primitive_types(left_type, right_type, node.operator)

        if node.operator.is_for_comparison():
            return self.__compare(left_type, right_type, node.operator)

        if node.operator.is_for_arithmetic():
            return self.__do_math(left_type, right_type, node.operator, node)

        raise ValueError(f"Where did you take this operator from?: {node.operator}")

    @staticmethod
    def __validate_primitive_types(left_type, right_type, operator):
        if not isinstance(left_type, DataType) or not isinstance(right_type, DataType):
            raise ValueError(f'Cannot use operator \'{operator}\' on struct types! '
                             f'Operators only work with primitive types (i32, i64, bool).')

    @staticmethod
    def __compare(left_type: DataType, right_type: DataType, operator) -> DataType:
        if (left_type == DataType.BOOL) != (right_type == DataType.BOOL):
            raise ValueError(f"You cannot compare using {operator} boolean with non-boolean!")
        return DataType.BOOL

    @staticmethod
    def __do_math(left_type: DataType, right_type: DataType, operator, node) -> DataType:
        if left_type == DataType.BOOL or right_type == DataType.BOOL:
            raise ValueError(f"You cannot play math using {operator} on booleans!!!")

        result_type = DataType.I64 if (left_type == DataType.I64 or right_type == DataType.I64) else DataType.I32
        node.result_type = result_type
        return result_type

    def visit_id(self, node: IDNode):
        if self.context.currently_initializing == node.value:
            raise ValueError(f"Self-assignment like '{node.value} = {node.value}' is not allowed at line {node.line}!")

        self.__check_variable_declared(node.value, node.line)
        return self.context.get_variable_type(node.value)

    def visit_number(self, node: NumberNode) -> DataType:
        value = int(node.value)
        return DataType.I32 if I32_MIN <= value <= I32_MAX else DataType.I64

    def visit_boolean(self, node: BooleanNode) -> DataType:
        return DataType.BOOL

    def visit_if_statement(self, node):
        condition_type = node.condition.accept(self)
        if condition_type != DataType.BOOL:
            raise ValueError(f"If condition must be of type bool, but you placed {condition_type} at line {node.line}! "
                             f"How could you????????")

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
                raise ValueError(f"The NOT operator (!) can only be applied to the boolean values, dummy, "
                                 f"but you applied it to {operand_type}! Do you think it is okay?")
            return DataType.BOOL
        raise ValueError(f"Unknown unary operator: {node.operator}")

    def __register_function(self, node: FunctionDeclNode):
        param_types = [p.param_type for p in node.params]
        self.context.define_function(node.variable, param_types, node.return_type)

    def visit_function_declaration(self, node: FunctionDeclNode):
        self.context.enter_scope()
        self.__declare_function_parameters(node)
        node.body.accept(self)
        self.__validate_function_return(node)
        self.context.exit_scope()

    def __declare_function_parameters(self, node: FunctionDeclNode):
        for param in node.params:
            # Resolve the parameter type to DataType if it's a primitive type
            param_type = self.__resolve_type(param.param_type)
            if not self.context.declare_variable(param.name, param_type, mutable=False):
                raise ValueError(f"Duplicate parameter '{param.name}' in function '{node.variable}'!")

    def __validate_function_return(self, node: FunctionDeclNode):
        if not node.body.return_node:
            raise ValueError(f"Function '{node.variable}' must have a return statement!")

        returned_type = node.body.return_node.expr_node.accept(self)
        expected_type = self.__resolve_type(node.return_type)
        
        if not self.__types_match(returned_type, expected_type):
            raise ValueError(f"Function '{node.variable}' returns {returned_type} but declared as {expected_type}!")

    def visit_function_call(self, node: FunctionCallNode):
        if not self.context.is_function_defined(node.value):
            raise ValueError(f"Function '{node.value}' not defined at line {node.line}!")

        func_info = self.context.get_function_info(node.value)
        self.__validate_argument_count(node, func_info)
        self.__validate_argument_types(node, func_info)

        return_type_str = func_info.return_type
        return self.__resolve_type(return_type_str)

    @staticmethod
    def __validate_argument_count(node: FunctionCallNode, func_info):
        if len(node.arguments) != len(func_info.param_types):
            raise ValueError(f"Function '{node.value}' expects {len(func_info.param_types)} arguments "
                             f"but got {len(node.arguments)} at line {node.line}!")

    def __validate_argument_types(self, node: FunctionCallNode, func_info):
        for i, (arg, expected_type_str) in enumerate(zip(node.arguments, func_info.param_types)):
            arg_type = arg.accept(self)
            expected_type = self.__resolve_type(expected_type_str)
            if not self.__types_match(arg_type, expected_type):
                raise ValueError(f"Argument {i + 1} to function '{node.value}' has type {arg_type} "
                                 f"but expected {expected_type} at line {node.line}!")

    def __types_match(self, expr_type, expected_type) -> bool:
        if isinstance(expected_type, DataType) and isinstance(expr_type, DataType):
            return self.__is_type_compatible(expr_type, expected_type)

        if isinstance(expected_type, str) and isinstance(expr_type, str):
            return expr_type == expected_type

        return False

    @staticmethod
    def __is_type_compatible(source_type: DataType, target_type: DataType) -> bool:
        return source_type == target_type or (source_type == DataType.I32 and target_type == DataType.I64)