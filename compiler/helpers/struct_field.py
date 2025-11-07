#!/usr/bin/env python3

class StructField:
    def __init__(self, data_type: str, variable: str, mutable: bool):
        self.data_type = data_type
        self.variable = variable
        self.mutable = mutable
