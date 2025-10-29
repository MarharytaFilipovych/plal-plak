#!/usr/bin/env python3
from enum import Enum


class Operator(Enum):
    PLUS = ('+', 'add')
    MINUS = ('-', 'sub')
    MULTIPLY = ('*', 'mul')
    EQUALS = ("==", 'icmp eq')
    NOT_EQUALS = ("!=", 'icmp ne')


    def __init__(self, symbol: str, llvm_operator: str):
        self.symbol = symbol
        self.llvm_operator = llvm_operator

    @staticmethod
    def from_string(op_str: str) -> 'Operator':
        for operator in Operator:
            if operator.symbol == op_str:
                return operator
        raise ValueError(f"This operator is not supported: {op_str}")

    def to_llvm(self) -> str:
        return self.llvm_operator

    def __str__(self) -> str:
        return self.symbol

    def is_for_comparison(self) -> bool:
        return self in (Operator.EQUALS, Operator.NOT_EQUALS)

    def is_for_arithmetic(self) -> bool:
        return self in (Operator.PLUS, Operator.MINUS, Operator.MULTIPLY)
