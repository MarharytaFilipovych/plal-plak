#!/usr/bin/env python3
from typing import Optional
from ..context.function_info import FunctionInfo


class FunctionTable:
    def __init__(self):
        self.functions: dict[str, dict[str, FunctionInfo]] = {}

    def add_function(self, scope: str, function_name: str, function_info: FunctionInfo):
        if scope not in self.functions:
            self.functions[scope] = {}
        self.functions[scope][function_name] = function_info

    def get_function_info(self, scope: str, function_name: str) -> Optional[FunctionInfo]:
        return self.functions.get(scope, {}).get(function_name)

    def scope_has_function(self, scope: str, function_name: str) -> bool:
        return function_name in self.functions.get(scope, {})

    def delete_function(self, scope: str, function_name: str):
        if scope in self.functions and function_name in self.functions[scope]:
            del self.functions[scope][function_name]

    def get_all_functions_in_scope(self, scope: str) -> list[tuple[str, FunctionInfo]]:
        functions_in_scope = self.functions.get(scope, {})
        return [(name, info) for name, info in functions_in_scope.items()]
