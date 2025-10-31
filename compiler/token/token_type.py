#!/usr/bin/env python3
from enum import Enum, auto


class TokenType(Enum):
    I32_TYPE = auto()
    MUT = auto()
    RETURN = auto()
    VARIABLE = auto()
    NUMBER = auto()
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    ASSIGNMENT = auto()
    LEFT_BRACKET = auto()
    RIGHT_BRACKET = auto()
    THE_END = auto()
    COMMENT = auto()
    NEWLINE = auto()
    FALSE = auto()
    TRUE = auto()
    I64_TYPE = auto()
    BOOL = auto()
    EQUALS = auto()
    NOT_EQUALS = auto()
    IF = auto()
    ELSE = auto()
    NOT = auto()
    STRUCT = auto()
    FN = auto()
    COMMA = auto()
    DOT = auto()

    @staticmethod
    def is_data_type(token_type: 'TokenType') -> bool:
        return token_type in {TokenType.I32_TYPE, TokenType.I64_TYPE, TokenType.BOOL}