#!/usr/bin/env python3
class Context:
    def __init__(self):
        self.declared_variables: dict[str, bool] = {}
        self.initialized_variables: set[str] = set()
        self.currently_initializing: str | None = None