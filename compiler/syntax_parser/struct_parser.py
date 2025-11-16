#!/usr/bin/env python3
from ..helpers.field_chain import FieldChain
from ..helpers.struct_field import StructField
from ..node.struct_decl_node import StructDeclNode
from ..node.struct_init_node import StructInitNode
from ..node.struct_field_node import StructFieldNode
from ..node.struct_field_assign_node import StructFieldAssignNode
from ..node.function_decl_node import FunctionDeclNode
from ..node.expr_node import ExprNode
from ..token.token_type import TokenType


class StructParser:
    def __init__(self, stream, declared_structs: set[str]):
        self.stream = stream
        self.declared_structs = declared_structs

    def parse_struct_declaration(self) -> StructDeclNode:
        self.stream.expect_token(TokenType.STRUCT)
        struct_token = self.stream.expect_token(TokenType.VARIABLE)
        struct_name = struct_token.value

        if struct_name in self.declared_structs:
            raise ValueError(f"The struct {struct_name} was already declared, you dummy!")

        self.declared_structs.add(struct_name)
        self.stream.consume_newline_and_skip()
        self.stream.expect_token(TokenType.LEFT_BRACKET)
        self.stream.consume_newline_and_skip()

        fields = self._parse_struct_fields()
        member_functions = self._parse_member_functions()

        self.stream.expect_token(TokenType.RIGHT_BRACKET)
        return StructDeclNode(struct_name, fields, member_functions, struct_token.line)

    def parse_struct_initialization(self, struct_type: str, line: int, expression_parser) -> StructInitNode:
        self.stream.expect_token(TokenType.LEFT_BRACKET)
        init_exprs: list[ExprNode] = []

        if self.stream.peek() and self.stream.peek().token_type != TokenType.RIGHT_BRACKET:
            init_exprs.append(expression_parser.parse_expression())

            while self.stream.peek() and self.stream.peek().token_type == TokenType.COMMA:
                self.stream.expect_token(TokenType.COMMA)
                init_exprs.append(expression_parser.parse_expression())

        self.stream.expect_token(TokenType.RIGHT_BRACKET)
        return StructInitNode(struct_type, init_exprs, line)

    def parse_field_assignment(self, variable_token, expression_parser) -> StructFieldAssignNode:
        field_chain = self._gather_field_accessors(variable_token.value)
        self.stream.expect_token(TokenType.ASSIGNMENT)
        value_expr = expression_parser.parse_expression()

        struct_field_node = StructFieldNode(FieldChain(field_chain), variable_token.line)
        return StructFieldAssignNode(struct_field_node, value_expr, variable_token.line)

    def parse_field_access(self, token, function_parser) -> StructFieldNode:
        from compiler.node.function_call_node import FunctionCallNode
        from compiler.constants import CALLABLE

        field_chain = self._gather_field_accessors(token.value)

        if self._is_function_call():
            func_name = field_chain[-1]
            object_chain = FieldChain(field_chain[:-1])
            return function_parser.parse_function_call(func_name, token.line, object_chain)

        return StructFieldNode(FieldChain(field_chain), token.line)

    def is_struct_type(self, token) -> bool:
        return token and token.token_type == TokenType.VARIABLE and token.value in self.declared_structs

    def _parse_struct_fields(self) -> list[StructField]:
        fields: list[StructField] = []
        while self.stream.peek() and self.stream.peek().token_type not in [TokenType.RIGHT_BRACKET, TokenType.FN]:
            var_type = self._parse_type()
            can_mutate = self._parse_mutability()
            token_variable = self.stream.expect_token(TokenType.VARIABLE)
            fields.append(StructField(var_type, token_variable.value, can_mutate))
            self.stream.consume_newline_and_skip()
        return fields

    def _parse_member_functions(self) -> list[FunctionDeclNode]:
        from .function_parser import FunctionParser

        member_functions = []
        while self.stream.peek() and self.stream.peek().token_type == TokenType.FN:
            # We need to access the parent parser's function_parser
            # This will be set up properly in the parent parser
            member_functions.append(None)  # Placeholder - handled in main parser
            self.stream.consume_newline_and_skip()
        return member_functions

    def _parse_type(self) -> str:
        token = self.stream.peek()

        if (TokenType.is_data_type(token.token_type)) or \
                (token.token_type == TokenType.VARIABLE and token.value in self.declared_structs):
            self.stream.eat()
            return token.value
        raise ValueError(
            f"I expected some type declaration at line {token.line} but I cannot recognize this type: {token.value}!")

    def _parse_mutability(self) -> bool:
        if self.stream.peek() and self.stream.peek().token_type == TokenType.MUT:
            self.stream.eat()
            return True
        return False

    def _gather_field_accessors(self, base_variable: str) -> list[str]:
        field_chain = [base_variable]

        while self._is_field_access():
            self.stream.expect_token(TokenType.DOT)
            field_token = self.stream.expect_token(TokenType.VARIABLE)
            field_chain.append(field_token.value)

        return field_chain

    def _is_field_access(self) -> bool:
        return self.stream.peek() and self.stream.peek().token_type == TokenType.DOT

    def _is_function_call(self) -> bool:
        return self.stream.peek() and self.stream.peek().token_type == TokenType.LEFT_DUZHKA