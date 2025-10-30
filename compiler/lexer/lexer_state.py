#!/usr/bin/env python3
from enum import Enum, auto


class LexerState(Enum):
    INITIAL = auto()
    VARIABLE = auto()
    NUMBER = auto()
    OPERATOR = auto()
    COMMENT = auto()
    WHITESPACE = auto()