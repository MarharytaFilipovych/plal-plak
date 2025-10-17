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
