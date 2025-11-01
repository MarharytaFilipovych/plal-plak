#!/usr/bin/env python3
from typing import Optional

from ..context.function_info import FunctionInfo
from ..llvm_specifics.data_type import DataType
from ..context.variable_info import VariableInfo
from ..node.struct_decl_node import StructField


class Context:
    def __init__(self):
        self.scopes: list[dict[str, VariableInfo]] = [{}]
        self.currently_initializing: Optional[str] = None
        self.struct_definitions: dict[str, list[StructField]] = {}
        self.functions: dict[str, FunctionInfo] = {}

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def declare_variable(self, name: str, data_type: DataType | str, mutable: bool):
        current_scope = self.scopes[-1]
        if name in current_scope:
            return False

        current_scope[name] = VariableInfo(data_type, mutable)
        return True

    def lookup_variable(self, name: str) -> Optional[VariableInfo]:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def is_declared_in_current_scope(self, name: str) -> bool:
        return name in self.scopes[-1]

    def get_variable_type(self, name: str) -> Optional[DataType | str]:
        var_info = self.lookup_variable(name)
        return var_info.data_type if var_info else None

    def is_variable_mutable(self, name: str) -> bool:
        var_info = self.lookup_variable(name)
        return var_info.mutable if var_info else False

    def is_variable_declared(self, name: str) -> bool:
        return self.lookup_variable(name) is not None

    def define_struct(self, struct_name: str, fields: list[StructField]):
        self.struct_definitions[struct_name] = fields

    def is_struct_defined(self, struct_name: str) -> bool:
        return struct_name in self.struct_definitions

    def get_struct_definition(self, struct_name: str) -> list[StructField]:
        return [] if struct_name not in self.struct_definitions else self.struct_definitions[struct_name]

    def define_function(self, name: str, param_types: list[str], return_type: str):
        self.functions[name] = FunctionInfo(param_types, return_type)

    def is_function_defined(self, name: str) -> bool:
        return name in self.functions

    def get_function_info(self, name: str) -> FunctionInfo:
        return self.functions.get(name)