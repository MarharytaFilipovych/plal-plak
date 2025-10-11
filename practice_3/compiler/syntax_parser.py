#!/usr/bin/env python3
from .node.assign_node import AssignNode
from .node.binary_op_node import BinaryOpNode
from .node.decl_node import DeclNode
from .node.expr_node import ExprNode
from .node.factor_node import FactorNode
from .node.id_node import IDNode
from .node.number_node import NumberNode
from .node.program_node import ProgramNode
from .node.return_node import ReturnNode
from .node.stmt_node import StmtNode
from .operator import Operator
from .token.token_type import TokenType
from .token.token_class import Token


class SyntaxParser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current_token_index = 0

    def __peek(self) -> Token | None:
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
        statements = []

        while True:
            token = self.__peek()

            if not token:
                raise ValueError('Program must end with a "return" statement!')

            if token.token_type == TokenType.RETURN:
                break

            statement = self.__parse_statement()
            statements.append(statement)

        return_statement = self.__parse_return()
        return ProgramNode(statements, return_statement)

    def __parse_statement(self) -> StmtNode:
        token = self.__peek()

        if not token:
            raise ValueError("Why did you decide to abandon your work?! I want a statement!")

        if token.token_type == TokenType.I32_TYPE:
            return self.__parse_declaration()
        elif token.token_type == TokenType.VARIABLE:
            return self.__parse_assignment()
        else:
            raise ValueError(
                f"You should have either declared a variable or assign this cutie to sth at line {token.line}, "
                f"but you decided to use this token type: {token.token_type.name}"
            )

    def __parse_declaration(self) -> DeclNode:
        self.__expect_token(TokenType.I32_TYPE)

        can_mutate = False
        if self.__peek() and self.__peek().token_type == TokenType.MUT:
            can_mutate = True
            self.__eat()

        token_variable = self.__expect_token(TokenType.VARIABLE)
        variable = token_variable.value

        self.__expect_token(TokenType.LEFT_BRACKET)
        init_expr = self.__parse_expression()
        self.__expect_token(TokenType.RIGHT_BRACKET)

        return DeclNode(variable, init_expr, token_variable.line, can_mutate)

    def __parse_assignment(self) -> AssignNode:
        variable_token = self.__expect_token(TokenType.VARIABLE)
        variable = variable_token.value
        self.__expect_token(TokenType.ASSIGNMENT)
        value_expr = self.__parse_expression()
        return AssignNode(variable, value_expr, variable_token.line)

    def __parse_return(self) -> ReturnNode:
        self.__expect_token(TokenType.RETURN)
        return ReturnNode(self.__parse_expression())

    def __parse_expression(self) -> ExprNode:
        left_operand = self.__parse_factor()

        while True:
            token = self.__peek()
            if not token or token.token_type not in [TokenType.PLUS, TokenType.MINUS, TokenType.MULTIPLY]:
                break

            operator_token = self.__eat()
            operator = Operator.from_string(operator_token.value)
            right_operator = self.__parse_factor()

            left_operand = BinaryOpNode(left_operand, operator, right_operator)

        return left_operand

    def __parse_factor(self) -> FactorNode:
        token = self.__peek()

        if not token:
            raise ValueError(
                f"You should have used either a number or a variable, "
                f"but you decided to abandon your work! ")

        if token.token_type == TokenType.NUMBER:
            self.__eat()
            return NumberNode(token.value)
        elif token.token_type == TokenType.VARIABLE:
            self.__eat()
            return IDNode(token.value, token.line)
        else:
            raise ValueError(
                f"You should have used either a number or a variable "
                f"at line {token.line}, not {token.value}!")
