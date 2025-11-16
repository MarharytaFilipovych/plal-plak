#!/usr/bin/env python3
from typing import Union
from ..node.expr_node import ExprNode
from ..node.factor_node import FactorNode
from ..node.binary_op_node import BinaryOpNode
from ..node.unary_op_node import UnaryOpNode
from ..node.number_node import NumberNode
from ..node.bool_node import BooleanNode
from ..node.id_node import IDNode
from ..llvm_specifics.operator import Operator
from ..token.token_type import TokenType
from ..token.token_class import Token
from ..constants import NOT, CALLABLE
from ..helpers.field_chain import FieldChain


class ExpressionParser:
    def __init__(self, stream, parent_parser):
        self.stream = stream
        self.parent = parent_parser

    def parse_expression(self) -> ExprNode:
        left_operand = self.parse_factor()

        while True:
            token = self.stream.peek()
            if not token or not TokenType.is_operator(token.token_type):
                break

            operator_token = self.stream.eat()
            operator = Operator.from_string(operator_token.value)
            right_operator = self.parse_factor()
            left_operand = BinaryOpNode(left_operand, operator, right_operator)

        return left_operand

    def parse_factor(self) -> Union[FactorNode, UnaryOpNode]:
        token = self.stream.peek()

        if token and token.token_type == TokenType.NOT:
            self.stream.eat()
            operand = self.parse_factor()
            return UnaryOpNode(NOT, operand)

        return self._parse_primary()

    def _parse_primary(self) -> FactorNode:
        token = self.stream.peek()

        if not token:
            raise ValueError(f"You should have used either a number, a variable, or a boolean, "
                             f"but you decided to abandon your work!")

        match token.token_type:
            case TokenType.NUMBER:
                self.stream.eat()
                return NumberNode(token.value)
            case TokenType.VARIABLE:
                return self._parse_token_variable(token)
            case TokenType.TRUE | TokenType.FALSE:
                self.stream.eat()
                return BooleanNode(token.value)
            case _:
                raise ValueError(f"You should have used either a number, a variable, or a boolean "
                                 f"at line {token.line}, not {token.value}!")

    def _parse_token_variable(self, token: Token) -> FactorNode:
        self.stream.eat()

        # Check for field access
        if self._is_field_access():
            return self.parent.struct_parser.parse_field_access(token, self.parent.function_parser)

        # Check for function call
        if self._is_function_call():
            if token.value in self.parent.declared_structs:
                synthetic_chain = FieldChain([token.value])
                return self.parent.function_parser.parse_function_call(CALLABLE, token.line, synthetic_chain)
            return self.parent.function_parser.parse_function_call(token.value, token.line)

        # Check for struct initialization
        if self._is_struct_initialization(token.value):
            return self.parent.struct_parser.parse_struct_initialization(
                token.value, token.line, self
            )

        # Simple identifier
        return IDNode(token.value, token.line)

    def _is_struct_initialization(self, value: str) -> bool:
        return (self.stream.peek() and
                self.stream.peek().token_type == TokenType.LEFT_BRACKET and
                value in self.parent.declared_structs)

    def _is_field_access(self) -> bool:
        return self.stream.peek() and self.stream.peek().token_type == TokenType.DOT

    def _is_function_call(self) -> bool:
        return self.stream.peek() and self.stream.peek().token_type == TokenType.LEFT_DUZHKA