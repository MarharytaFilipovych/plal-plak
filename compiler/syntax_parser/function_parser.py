#!/usr/bin/env python3
from typing import Optional
from ..node.function_decl_node import FunctionDeclNode, FunctionParam
from ..node.function_call_node import FunctionCallNode
from ..node.code_block_node import CodeBlockNode
from ..helpers.field_chain import FieldChain
from ..token.token_type import TokenType


class FunctionParser:
    def __init__(self, stream, parent_parser):
        self.stream = stream
        self.parent = parent_parser

    def parse_function_declaration(self) -> FunctionDeclNode:
        self.stream.expect_token(TokenType.FN)
        func_name_token = self.stream.expect_token(TokenType.VARIABLE)
        self.stream.expect_token(TokenType.ASSIGNMENT)

        params = self._parse_parenthesized_list(self._parse_function_param)

        self.stream.expect_token(TokenType.ARROW)
        return_type = self.parse_type(self.stream, self.parent.declared_structs)
        self.stream.consume_newline_and_skip()
        body = self._parse_code_block()

        return FunctionDeclNode(func_name_token.value, params, return_type, body, func_name_token.line)

    def parse_function_call(self, func_name: str, line: int,
                           field_chain: Optional[FieldChain] = None) -> FunctionCallNode:
        arguments = self._parse_parenthesized_list(self.parent.expression_parser.parse_expression)
        return FunctionCallNode(func_name, arguments, line, field_chain)

    def _parse_function_param(self) -> FunctionParam:
        param_type = self.parse_type(self.stream, self.parent.declared_structs)
        param_name = self.stream.expect_token(TokenType.VARIABLE).value
        return FunctionParam(param_type, param_name)

    def _parse_code_block(self) -> CodeBlockNode:
        self.stream.expect_token(TokenType.LEFT_BRACKET)
        self.stream.consume_newline_and_skip()

        statements, return_node = self.parent.statement_parser.parse_block_contents()

        self.stream.expect_token(TokenType.RIGHT_BRACKET)
        scope_id = self.parent.allocate_scope_id()
        return CodeBlockNode(statements, return_node, scope_id)

    @staticmethod
    def parse_type(stream, declared_structs) -> str:
        token = stream.peek()

        if (TokenType.is_data_type(token.token_type)) or \
                (token.token_type == TokenType.VARIABLE and token.value in declared_structs):
            stream.eat()
            return token.value
        raise ValueError(
            f"I expected some type declaration at line {token.line} but I cannot recognize this type: {token.value}!")

    def _parse_parenthesized_list(self, parse_item_fn):
        self.stream.expect_token(TokenType.LEFT_DUZHKA)
        items = []

        if self.stream.peek().token_type != TokenType.RIGHT_DUZHKA:
            items.append(parse_item_fn())
            while self.stream.peek() and self.stream.peek().token_type == TokenType.COMMA:
                self.stream.eat()
                items.append(parse_item_fn())

        self.stream.expect_token(TokenType.RIGHT_DUZHKA)
        return items