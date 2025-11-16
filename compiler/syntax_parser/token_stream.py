#!/usr/bin/env python3
from ..token.token_class import Token
from ..token.token_type import TokenType


class TokenStream:

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current_index = 0

    def peek(self) -> Token:
        return self.tokens[self.current_index] if self.current_index < len(self.tokens) else None

    def eat(self) -> Token:
        token = self.peek()
        if token:
            self.current_index += 1
        return token

    def expect_token(self, token_type: TokenType) -> Token:
        token = self.peek()
        if not token:
            raise ValueError(f"I expected a token of the type {token_type.name} "
                             f"but you decided to abandon this promising code!")

        if token.token_type != token_type:
            raise ValueError(f"I expected a token of the type {token_type.name} but you gave me '{token.value}' "
                             f"at line {token.line}!!!")

        return self.eat()

    def skip_newlines(self):
        while self.peek() and self.peek().token_type == TokenType.NEWLINE:
            self.eat()

    def expect_newline_or_end(self):
        token = self.peek()
        if token and token.token_type not in [TokenType.NEWLINE, TokenType.THE_END]:
            raise ValueError(
                f"Each instruction must be on its own line! "
                f"You were expected to place a newline after the"
                f" instruction at line {token.line}, but you placed this: {token.value}")
        if token and token.token_type == TokenType.NEWLINE:
            self.eat()

    def consume_newline_and_skip(self):
        self.expect_newline_or_end()
        self.skip_newlines()

    def save_position(self) -> int:
        return self.current_index

    def restore_position(self, position: int):
        self.current_index = position