#!/usr/bin/env python3
import os.path
import sys
from .lexer.lexer import Lexer
import argparse
from .visitor.code_generator import CodeGenerator
from .visitor.semantic_analyzer import SemanticAnalyzer
from .syntax_parser import SyntaxParser


class Compiler:
    def __init__(self):
        self.input_file, self.output_file = self.__parse_arguments()

    @staticmethod
    def __parse_arguments() -> tuple[str, str]:
        parser = argparse.ArgumentParser()
        parser.add_argument('input_file', help="Input file that contains source code")
        parser.add_argument('output_file', help="Output LLVM IR file")
        args = parser.parse_args()

        if not os.path.exists(args.input_file):
            print(f"File '{args.input_file}' was not found!")
            sys.exit(1)

        return args.input_file, args.output_file

    @staticmethod
    def __read_source_file(file_name: str) -> str:
        with open(file_name, 'r') as file:
            return file.read()

    @staticmethod
    def __write_output_file(file_name: str, content: str):
        with open(file_name, 'w') as file:
            file.write(content)

    @staticmethod
    def __get_tokens(source_code: str) -> list:
        lexer = Lexer(source_code)
        return lexer.tokenize()

    @staticmethod
    def __get_ast(tokens: list):
        parser = SyntaxParser(tokens)
        return parser.parse_program()

    @staticmethod
    def __analyze_semantics(ast):
        semantic_analyzer = SemanticAnalyzer()
        ast.accept(semantic_analyzer)

    @staticmethod
    def __generate_code(ast) -> str:
        code_generator = CodeGenerator()
        return ast.accept(code_generator)

    def __compile(self) -> str:
        source_code = self.__read_source_file(self.input_file)
        tokens = self.__get_tokens(source_code)
        ast = self.__get_ast(tokens)
        self.__analyze_semantics(ast)
        llvm_ir = self.__generate_code(ast)
        return llvm_ir

    def run_program(self):
        try:
            translated_code = self.__compile()
            self.__write_output_file(self.output_file, translated_code)
            print(f"Successfully compiled '{self.input_file}' to '{self.output_file}'")
            sys.exit(0)

        except ValueError as e:
            print(f"OHHHH NOOOO, compilation failed: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error :((((: {e}")
            sys.exit(1)


compiler = Compiler()
compiler.run_program()