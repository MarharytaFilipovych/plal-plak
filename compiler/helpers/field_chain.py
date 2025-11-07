#!/usr/bin/env python3

class FieldChain:
    def __init__(self, chain: list[str]):
        self.fields = chain

    def __str__(self):
        return ".".join(self.fields)
