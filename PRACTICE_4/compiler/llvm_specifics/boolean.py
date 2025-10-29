#!/usr/bin/env python3
from enum import Enum


class Boolean(Enum):
    FALSE = ("false", "0")
    TRUE = ("true", "1")

    def __init__(self, boolean: str, llvm_representation: str):
        self.boolean = boolean
        self.llvm_representation = llvm_representation

    @staticmethod
    def from_string(bool_str: str) -> 'Boolean':
        for b in Boolean:
            if b.boolean == bool_str:
                return b
        raise ValueError(f"This boolean value does not exist: {bool_str}")

    def to_llvm(self) -> str:
        return self.llvm_representation

    def __str__(self) -> str:
        return self.boolean
