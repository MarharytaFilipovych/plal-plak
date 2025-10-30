#!/usr/bin/env python3
from typing import Optional

from .llvm_specifics.data_type import DataType
from .variable_info import VariableInfo


class Context:
    def __init__(self):
        self.scopes: list[dict[str, VariableInfo]] = [{}]
        self.currently_initializing: Optional[str]

    def enter_scope(self) -> int:
        self.scopes.append({})

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def declare_variable(self, name: str, data_type: DataType, mutable: bool):
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

    def get_variable_type(self, name: str) -> Optional[DataType]:
        var_info = self.lookup_variable(name)
        return var_info.data_type if var_info else None

    def is_variable_mutable(self, name: str) -> bool:
        var_info = self.lookup_variable(name)
        return var_info.mutable if var_info else False

    def is_variable_declared(self, name: str) -> bool:
        return self.lookup_variable(name) is not None
