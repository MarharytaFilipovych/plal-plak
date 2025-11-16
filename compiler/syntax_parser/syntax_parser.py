#!/usr/bin/env python3
from ..node.program_node import ProgramNode
from ..token.token_class import Token
from ..token.token_type import TokenType
from .token_stream import TokenStream
from .struct_parser import StructParser
from .function_parser import FunctionParser
from .statement_parser import StatementParser
from .expression_parser import ExpressionParser


class SyntaxParser:
    def __init__(self, tokens: list[Token]):
        self.stream = TokenStream(tokens)
        self.declared_structs: set[str] = set()
        self.next_scope_id = 1

        self.struct_parser = StructParser(self.stream, self.declared_structs)
        self.function_parser = FunctionParser(self.stream, self)
        self.expression_parser = ExpressionParser(self.stream, self)
        self.statement_parser = StatementParser(self.stream, self)

    def parse_program(self) -> ProgramNode:
        self.stream.skip_newlines()

        struct_declarations = self._parse_declaration_block(
            TokenType.STRUCT,
            self.struct_parser.parse_struct_declaration
        )

        func_declarations = self._parse_declaration_block(
            TokenType.FN,
            self.function_parser.parse_function_declaration
        )

        statements = self.statement_parser.parse_statements()
        return_statement = self.statement_parser.parse_program_return()
        self._check_program_end()

        return ProgramNode(struct_declarations, func_declarations, statements, return_statement)

    def _parse_declaration_block(self, start_token_type, parse_function):
        decls = []
        while self.stream.peek() and self.stream.peek().token_type == start_token_type:
            decls.append(parse_function())
            self.stream.consume_newline_and_skip()
        return decls

    def _check_program_end(self):
        if self.stream.peek() and self.stream.peek().token_type != TokenType.THE_END:
            raise ValueError(
                f"I did not want you to place this awful content "
                f"after the return statement at line {self.stream.peek().line}")

    def allocate_scope_id(self) -> int:
        scope_id = self.next_scope_id
        self.next_scope_id += 1
        return scope_id