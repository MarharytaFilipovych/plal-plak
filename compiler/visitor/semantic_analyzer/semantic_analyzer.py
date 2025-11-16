#!/usr/bin/env python3
from ..ast_visitor import ASTVisitor
from compiler.context.context import Context
from ...constants import GLOBAL_SCOPE
from ...llvm_specifics.data_type import DataType
from ...node.program_node import ProgramNode
from ...node.code_block_node import CodeBlockNode
from .struct_analyzer import StructAnalyzer
from .variable_analyzer import VariableAnalyzer
from .expression_analyzer import ExpressionAnalyzer
from .function_analyzer import FunctionAnalyzer


class SemanticAnalyzer(ASTVisitor):
    def __init__(self):
        self.context = Context()
        self._expected_return_type = None
        self._function_name = None
        self._current_struct_context = None

        self.struct_analyzer = StructAnalyzer(self.context, self)
        self.variable_analyzer = VariableAnalyzer(self.context, self)
        self.expression_analyzer = ExpressionAnalyzer(self.context, self)
        self.function_analyzer = FunctionAnalyzer(self.context, self)

    def visit_program(self, node: ProgramNode):
        [struct_decl.accept(self) for struct_decl in node.struct_decls]
        [self.function_analyzer.register_function(GLOBAL_SCOPE, func_decl) for func_decl in node.func_decls]
        [func_decl.accept(self) for func_decl in node.func_decls]
        [stmt.accept(self) for stmt in node.statement_nodes]
        node.return_node.accept(self)

    def visit_struct_declaration(self, node):
        self.struct_analyzer.visit_struct_declaration(node)

    def visit_struct_initialization(self, node):
        return self.struct_analyzer.visit_struct_initialization(node)

    def visit_struct_field(self, node):
        return self.struct_analyzer.visit_struct_field(node)

    def visit_struct_field_assignment(self, node):
        self.struct_analyzer.visit_struct_field_assignment(node)

    def visit_declaration(self, node):
        self.variable_analyzer.visit_declaration(node)

    def visit_assignment(self, node):
        self.variable_analyzer.visit_assignment(node)

    def visit_id(self, node):
        return self.variable_analyzer.visit_id(node)

    def visit_number(self, node):
        return self.expression_analyzer.visit_number(node)

    def visit_boolean(self, node):
        return self.expression_analyzer.visit_boolean(node)

    def visit_binary_operation(self, node):
        return self.expression_analyzer.visit_binary_operation(node)

    def visit_unary_operation(self, node):
        return self.expression_analyzer.visit_unary_operation(node)

    def visit_function_declaration(self, node):
        self.function_analyzer.visit_function_declaration(node, self)

    def visit_function_call(self, node):
        return self.function_analyzer.visit_function_call(node, self._current_struct_context)

    def visit_return(self, node):
        returned_type = node.expr_node.accept(self)

        if self._expected_return_type is not None:
            if not self.expression_analyzer.types_match(returned_type, self._expected_return_type):
                raise ValueError(f"Function '{self._function_name}' returns {returned_type} "
                                 f"but declared as {self._expected_return_type}!")

        return returned_type

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
        [n.accept(self) for n in node.statements]
        if node.return_node:
            node.return_node.accept(self)
        self.context.exit_scope()