#!/usr/bin/env python3
from typing import Union

from compiler.llvm_specifics.data_type import DataType


class VariableInfo:
    def __init__(self, data_type: Union[DataType, str], mutable: bool):
        self.data_type = data_type
        self.mutable = mutable
