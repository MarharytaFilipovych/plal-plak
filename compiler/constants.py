#!/usr/bin/env python3
from .token.token_type import TokenType

I32_MIN = -2147483648
I32_MAX = 2147483647

NOT = '!'
WHITESPACE = ' \t\r'
OPERATORS = '+-*='

KEYWORDS: dict = {
    "i32": TokenType.I32_TYPE,
    "mut": TokenType.MUT,
    "return": TokenType.RETURN,
    "false": TokenType.FALSE,
    "true": TokenType.TRUE,
    "i64": TokenType.I64_TYPE,
    "bool": TokenType.BOOL,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "struct": TokenType.STRUCT,
    "fn": TokenType.FN
}

PREDEFINED_CHARS: dict = {
    '{': TokenType.LEFT_BRACKET,
    '}': TokenType.RIGHT_BRACKET,
    '+': TokenType.PLUS,
    '*': TokenType.MULTIPLY,
    ',': TokenType.COMMA,
    '.': TokenType.DOT,
    '(': TokenType.LEFT_PAREN,
    ')': TokenType.RIGHT_PAREN
}