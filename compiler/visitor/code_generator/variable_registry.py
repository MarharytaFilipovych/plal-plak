#!/usr/bin/env python3
from typing import Union, Optional
from ...llvm_specifics.data_type import DataType


class VariableRegistry:
    def __init__(self):
        self.variable_versions: dict[str, int] = {}
        self.variable_types: dict[str, Union[DataType, str]] = {}
        self.max_versions: dict[str, int] = {}

    def get_variable_register(self, variable: str) -> str:
        if variable not in self.max_versions:
            self.max_versions[variable] = 0
            self.variable_versions[variable] = 0
            return f"%{variable}"

        self.max_versions[variable] += 1
        self.variable_versions[variable] = self.max_versions[variable]
        return f"%{variable}.{self.variable_versions[variable]}"

    def get_current_register(self, variable: str) -> str:
        if variable not in self.variable_versions or self.variable_versions[variable] == 0:
            return f"%{variable}"
        return f"%{variable}.{self.variable_versions[variable]}"

    def get_variable_type(self, variable: str) -> Optional[Union[DataType, str]]:
        return self.variable_types.get(variable)

    def set_variable_type(self, variable: str, var_type: Union[DataType, str]):
        self.variable_types[variable] = var_type

    def set_variable_version(self, variable: str, version: int):
        self.variable_versions[variable] = version

    def get_variable_version(self, variable: str) -> Optional[int]:
        return self.variable_versions.get(variable)

    def is_field_access_from_this(self, variable: str) -> bool:
        return self.variable_versions.get(variable) == -1

    def copy_state(self) -> dict:
        return {
            'versions': self.variable_versions.copy(),
            'types': self.variable_types.copy(),
            'max_versions': self.max_versions.copy()
        }

    def restore_state(self, state: dict):
        self.variable_versions = state['versions']
        self.variable_types = state['types']
        self.max_versions = state['max_versions']

    def reset(self):
        self.variable_versions = {}
        self.variable_types = {}
        self.max_versions = {}