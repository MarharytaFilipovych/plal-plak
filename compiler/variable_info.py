#!/usr/bin/env python3
from .llvm_specifics.data_type import DataType

class VariableInfo:
    def __init__(self, data_type: DataType, mutable: bool):
        self.data_type = data_type
        self.mutable = mutable