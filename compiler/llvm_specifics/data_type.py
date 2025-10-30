#!/usr/bin/env python3
from enum import Enum


class DataType(Enum):
    I32 = ("i32", "i32")
    I64 = ("i64", "i64")
    BOOL = ("bool", "i1")

    def __init__(self, keyword: str, llvm_representation: str):
        self.keyword = keyword
        self.llvm_representation = llvm_representation

    @staticmethod
    def from_string(type_str: str) -> 'DataType':
        for data_type in DataType:
            if data_type.keyword == type_str:
                return data_type
        raise ValueError(f"This type does not exist: {type_str}")

    def to_llvm(self) -> str:
        return self.llvm_representation

    def __str__(self) -> str:
        return self.keyword

    @staticmethod
    def is_data_type(type_str: str) -> bool:
        return any(data_type.keyword == type_str for data_type in DataType)