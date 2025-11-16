#!/usr/bin/env python3
from typing import Optional
from compiler.node.stmt_node import StmtNode
from compiler.node.decl_node import DeclNode
from compiler.node.assign_node import AssignNode
from compiler.node.return_node import ReturnNode
from compiler.node.if_node import IfNode
from compiler.node.code_block_node import CodeBlockNode
from compiler.llvm_specifics.data_type import DataType
from compiler.syntax_parser.function_parser import FunctionParser
from compiler.token.token_type import TokenType


class StatementParser:
    def __init__(self, stream, parent_parser):
        self.stream = stream
        self.parent = parent_parser

    def parse_statements(self) -> list[StmtNode]:
        statements = []

        while True:
            token = self.stream.peek()

            if not token or token.token_type == TokenType.THE_END:
                raise ValueError('Program must end with a "return" statement!')

            if token.token_type == TokenType.RETURN:
                break

            statement = self.parse_statement()
            statements.append(statement)
            self.stream.consume_newline_and_skip()

        return statements

    def parse_program_return(self) -> ReturnNode:
        return_statement = self._parse_return()
        self.stream.skip_newlines()
        return return_statement

    def parse_statement(self) -> StmtNode:
        token = self.stream.peek()

        if not token:
            raise ValueError("Why did you decide to abandon your work?! I want a statement!")

        if token.token_type == TokenType.STRUCT:
            return self.parent.struct_parser.parse_struct_declaration()
        elif TokenType.is_data_type(token.token_type):
            return self._parse_variable_declaration()
        elif token.token_type == TokenType.VARIABLE:
            if self.parent.struct_parser.is_struct_type(token):
                return self._parse_variable_declaration()
            return self._parse_assignment()
        elif token.token_type == TokenType.IF:
            return self._parse_if_statement()
        else:
            raise ValueError(f"You should have either declared a variable or assign this "
                             f"cutie to sth at line {token.line}, "
                             f"but you decided to use this token type: {token.value}")

    def parse_block_contents(self) -> tuple[list[StmtNode], Optional[ReturnNode]]:
        statements = []
        return_node = None

        while True:
            token = self.stream.peek()

            if not token:
                raise ValueError("Code block must end with }!")

            if token.token_type == TokenType.RIGHT_BRACKET:
                break

            if token.token_type == TokenType.RETURN:
                return_node = self._parse_return()
                self.stream.consume_newline_and_skip()
                self._check_no_code_after_return()
                break

            statement = self.parse_statement()
            statements.append(statement)
            self.stream.consume_newline_and_skip()

        return statements, return_node

    def _parse_variable_declaration(self) -> DeclNode:
        var_type = FunctionParser.parse_type(self.stream, self.parent.declared_structs)
        can_mutate = self._parse_mutability()
        token_variable = self.stream.expect_token(TokenType.VARIABLE)

        init_expr = self.parent.struct_parser.parse_struct_initialization(
            var_type, token_variable.line, self.parent.expression_parser
        ) if var_type in self.parent.declared_structs else self._parse_initializer()

        data_type = DataType.from_string(var_type) if var_type in ["i32", "i64", "bool"] else var_type
        return DeclNode(token_variable.value, init_expr, token_variable.line, can_mutate, data_type)

    def _parse_assignment(self) -> AssignNode:
        variable_token = self.stream.expect_token(TokenType.VARIABLE)

        # Check if this is a field assignment
        if self._is_field_access():
            return self.parent.struct_parser.parse_field_assignment(
                variable_token, self.parent.expression_parser
            )

        # Simple variable assignment
        self.stream.expect_token(TokenType.ASSIGNMENT)
        value_expr = self.parent.expression_parser.parse_expression()
        return AssignNode(variable_token.value, value_expr, variable_token.line)

    def _parse_if_statement(self) -> IfNode:
        if_token = self.stream.expect_token(TokenType.IF)
        condition = self.parent.expression_parser.parse_expression()
        self.stream.consume_newline_and_skip()

        then_block = self._parse_code_block()
        else_block = self._try_parse_else_block()

        return IfNode(condition, then_block, else_block, if_token.line)

    def _parse_return(self) -> ReturnNode:
        self.stream.expect_token(TokenType.RETURN)
        return ReturnNode(self.parent.expression_parser.parse_expression())

    def _parse_mutability(self) -> bool:
        if self.stream.peek() and self.stream.peek().token_type == TokenType.MUT:
            self.stream.eat()
            return True
        return False

    def _parse_initializer(self):
        self.stream.expect_token(TokenType.LEFT_BRACKET)
        init_expr = self.parent.expression_parser.parse_expression()
        self.stream.expect_token(TokenType.RIGHT_BRACKET)
        return init_expr

    def _parse_code_block(self) -> CodeBlockNode:
        self.stream.expect_token(TokenType.LEFT_BRACKET)
        self.stream.consume_newline_and_skip()

        statements, return_node = self.parse_block_contents()

        self.stream.expect_token(TokenType.RIGHT_BRACKET)
        scope_id = self.parent.allocate_scope_id()
        return CodeBlockNode(statements, return_node, scope_id)

    def _try_parse_else_block(self) -> Optional[CodeBlockNode]:
        token = self.stream.peek()

        if not token or token.token_type != TokenType.NEWLINE:
            return None

        saved_pos = self.stream.save_position()
        self.stream.eat()
        self.stream.skip_newlines()

        if self.stream.peek() and self.stream.peek().token_type == TokenType.ELSE:
            self.stream.eat()
            self.stream.consume_newline_and_skip()
            return self._parse_code_block()
        else:
            self.stream.restore_position(saved_pos)
            return None

    def _check_no_code_after_return(self):
        next_token = self.stream.peek()
        if next_token and next_token.token_type != TokenType.RIGHT_BRACKET:
            raise ValueError(f"Code after return statement is not allowed at line {next_token.line}!")

    def _is_field_access(self) -> bool:
        return self.stream.peek() and self.stream.peek().token_type == TokenType.DOT