#!/usr/bin/env python3
from .llvm_specifics.data_type import DataType


class Context:
    def __init__(self):
        self.declared_variables: dict[str, bool] = {}
        self.initialized_variables: set[str] = set()
        self.currently_initializing: str | None = None
        self.variable_types: dict[str, DataType] = {}