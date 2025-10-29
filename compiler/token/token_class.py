#!/usr/bin/env python3
from .token_type import TokenType


class Token:
    def __init__(self, token_type: TokenType, value: str, line=0, index=0):
        self.token_type = token_type
        self.value = value
        self.line = line
        self.index = index

    def __repr__(self):
        return f"Token({self.token_type.name}, '{self.value}', line={self.line}, col={self.index})"

    def __str__(self):
        return (f"Token of the type {self.token_type.name} with the value '{self.value}. "
                f"Located on the line {self.line} and column {self.index}'")