#!/usr/bin/env python3
from typing import Union, Optional

from .node.assign_node import AssignNode
from .node.binary_op_node import BinaryOpNode
from .node.code_block_node import CodeBlockNode
from .node.decl_node import DeclNode
from .node.expr_node import ExprNode
from .node.factor_node import FactorNode
from .node.id_node import IDNode
from .node.if_node import IfNode
from .node.number_node import NumberNode
from .node.program_node import ProgramNode
from .node.return_node import ReturnNode
from .node.stmt_node import StmtNode
from .llvm_specifics.data_type import DataType
from .llvm_specifics.operator import Operator
from .node.bool_node import BooleanNode
from .node.unary_op_node import UnaryOpNode
from .token.token_type import TokenType
from .token.token_class import Token


class SyntaxParser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current_token_index = 0
        self.next_scope_id = 1

    def __peek(self) -> Token:
        return self.tokens[self.current_token_index] if self.current_token_index < len(self.tokens) else None

    def __eat(self) -> Token:
        token = self.__peek()
        if token:
            self.current_token_index += 1
        return token

    def __expect_token(self, token_type: TokenType) -> Token:
        token = self.__peek()
        if not token:
            raise ValueError(
                f"I expected a token of the type {token_type.name} but you decided to abandon this promising code!")

        if token.token_type != token_type:
            raise ValueError(
                f"I expected a token of the type {token_type.name} but you gave me {token.token_type.name} "
                f"at line {token.line} and index {token.index}")

        return self.__eat()

    def parse_program(self) -> ProgramNode:
        self.__skip_newlines()
        statements = self.__parse_statements()
        return_statement = self.__parse_program_return()
        self.__check_program_end()

        return ProgramNode(statements, return_statement)

    def __parse_statements(self) -> list[StmtNode]:
        statements = []

        while True:
            token = self.__peek()

            if not token or token.token_type == TokenType.THE_END:
                raise ValueError('Program must end with a "return" statement!')

            if token.token_type == TokenType.RETURN:
                break

            statement = self.__parse_statement()
            statements.append(statement)
            self.__consume_newline_and_skip()

        return statements

    def __parse_program_return(self) -> ReturnNode:
        return_statement = self.__parse_return()
        self.__skip_newlines()
        return return_statement

    def __check_program_end(self):
        if self.__peek() and self.__peek().token_type != TokenType.THE_END:
            raise ValueError(
                f"I did not want you to place this awful content "
                f"after the return statement at line {self.__peek().line}")

    def __parse_statement(self) -> StmtNode:
        token = self.__peek()

        if not token:
            raise ValueError("Why did you decide to abandon your work?! I want a statement!")

        if token.token_type in [TokenType.I32_TYPE, TokenType.I64_TYPE, TokenType.BOOL]:
            return self.__parse_declaration()
        elif token.token_type == TokenType.VARIABLE:
            return self.__parse_assignment()
        elif token.token_type == TokenType.IF:
            return self.__parse_if_statement()
        else:
            raise ValueError(
                f"You should have either declared a variable or assign this cutie to sth at line {token.line}, "
                f"but you decided to use this token type: {token.token_type.name}")

    def __skip_newlines(self):
        while self.__peek() and self.__peek().token_type == TokenType.NEWLINE:
            self.__eat()

    def __expect_newline_or_end(self):
        token = self.__peek()
        if token and token.token_type not in [TokenType.NEWLINE, TokenType.THE_END]:
            raise ValueError(
                f"Each instruction must be on its own line! "
                f"You were expected to place a newline after the"
                f" instruction at line {token.line}, but you placed this: {token.token_type.name}")
        if token and token.token_type == TokenType.NEWLINE:
            self.__eat()

    def __consume_newline_and_skip(self):
        self.__expect_newline_or_end()
        self.__skip_newlines()

    def __parse_declaration(self) -> DeclNode:
        var_type = self.__parse_type()
        can_mutate = self.__parse_mutability()
        token_variable = self.__expect_token(TokenType.VARIABLE)
        variable = token_variable.value
        init_expr = self.__parse_initializer()

        return DeclNode(variable, init_expr, token_variable.line, can_mutate, var_type)

    def __parse_type(self) -> DataType:
        type_token = self.__peek()

        if type_token.token_type not in [TokenType.I32_TYPE, TokenType.I64_TYPE, TokenType.BOOL]:
            raise ValueError(f"I expected some type declaration at line {type_token.line}!")

        var_type = DataType.from_string(type_token.value)
        self.__eat()
        return var_type

    def __parse_mutability(self) -> bool:
        if self.__peek() and self.__peek().token_type == TokenType.MUT:
            self.__eat()
            return True
        return False

    def __parse_initializer(self) -> ExprNode:
        self.__expect_token(TokenType.LEFT_BRACKET)
        init_expr = self.__parse_expression()
        self.__expect_token(TokenType.RIGHT_BRACKET)
        return init_expr

    def __parse_assignment(self) -> AssignNode:
        variable_token = self.__expect_token(TokenType.VARIABLE)
        variable = variable_token.value
        self.__expect_token(TokenType.ASSIGNMENT)
        value_expr = self.__parse_expression()
        return AssignNode(variable, value_expr, variable_token.line)

    def __parse_if_statement(self) -> IfNode:
        if_token = self.__expect_token(TokenType.IF)
        condition = self.__parse_expression()
        self.__consume_newline_and_skip()

        then_block = self.__parse_code_block()
        else_block = self.__try_parse_else_block()

        return IfNode(condition, then_block, else_block, if_token.line)

    def __try_parse_else_block(self) -> Optional[CodeBlockNode]:
        token = self.__peek()

        if not token or token.token_type != TokenType.NEWLINE:
            return None

        saved_index = self.current_token_index
        self.__eat()
        self.__skip_newlines()

        if self.__peek() and self.__peek().token_type == TokenType.ELSE:
            self.__eat()
            self.__consume_newline_and_skip()
            return self.__parse_code_block()
        else:
            self.current_token_index = saved_index
            return None

    def __parse_code_block(self) -> CodeBlockNode:
        self.__expect_token(TokenType.LEFT_BRACKET)
        self.__consume_newline_and_skip()

        statements, return_node = self.__parse_block_contents()

        self.__expect_token(TokenType.RIGHT_BRACKET)
        scope_id = self.next_scope_id
        self.next_scope_id += 1
        return CodeBlockNode(statements, return_node, scope_id)

    def __parse_block_contents(self) -> tuple[list[StmtNode], ReturnNode | None]:
        statements = []
        return_node = None

        while True:
            token = self.__peek()

            if not token:
                raise ValueError("Code block must end with }!")

            if token.token_type == TokenType.RIGHT_BRACKET:
                break

            if token.token_type == TokenType.RETURN:
                return_node = self.__parse_return()
                self.__consume_newline_and_skip()
                self.__check_no_code_after_return()
                break

            statement = self.__parse_statement()
            statements.append(statement)
            self.__consume_newline_and_skip()

        return statements, return_node

    def __check_no_code_after_return(self):
        next_token = self.__peek()
        if next_token and next_token.token_type != TokenType.RIGHT_BRACKET:
            raise ValueError(
                f"Code after return statement is not allowed at line {next_token.line}!")

    def __parse_return(self) -> ReturnNode:
        self.__expect_token(TokenType.RETURN)
        return ReturnNode(self.__parse_expression())

    def __parse_expression(self) -> ExprNode:
        left_operand = self.__parse_factor()
        while True:
            token = self.__peek()
            if not token or token.token_type not in [
                TokenType.PLUS, TokenType.MINUS, TokenType.MULTIPLY,
                TokenType.EQUALS, TokenType.NOT_EQUALS]:
                break
            operator_token = self.__eat()
            operator = Operator.from_string(operator_token.value)
            right_operator = self.__parse_factor()
            left_operand = BinaryOpNode(left_operand, operator, right_operator)
        return left_operand

    def __parse_factor(self) -> Union[FactorNode, UnaryOpNode]:
        token = self.__peek()

        if token and token.token_type == TokenType.NOT:
            self.__eat()
            operand = self.__parse_factor()
            return UnaryOpNode("!", operand)

        return self.__parse_primary()

    def __parse_primary(self) -> FactorNode:
        token = self.__peek()

        if not token:
            raise ValueError(f"You should have used either a number, a variable, or a boolean, "
            f"but you decided to abandon your work!")
        token_type = token.token_type
        line = token.line
        value = token.value
        self.__eat()

        match token_type:
            case TokenType.NUMBER:
                return NumberNode(token.value)
            case TokenType.VARIABLE:
                return IDNode(token.value, token.line)
            case TokenType.TRUE | TokenType.FALSE:
                return BooleanNode(token.value)
            case _:
                raise ValueError(f"You should have used either a number, a variable, or a boolean "
                f"at line {line}, not {value}!")