#!/usr/bin/env python3
import os.path
import sys
from lexer import Lexer
import argparse
from token_class import Token
from token_type import TokenType


class Compiler:
    llvm_ir_operators = {
        '+': 'add',
        '-': 'sub',
        '*': 'mul'
    }

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current_token_index = 0
        self.declared_variables = {}
        self.initialized_variables = set()
        self.translated_lines = []
        self.variable_versions = {}

    @staticmethod
    def get_print_function_llvm() -> str:
        return """declare i32 @printf(i8*, ...)

@exit_format = private unnamed_addr constant [29 x i8] c"Program exit with result %d\\0A\\00", align 1

define void @printResult(i32 %val) {
  %fmt_ptr = getelementptr inbounds [29 x i8], [29 x i8]* @exit_format, i32 0, i32 0
  call i32 (i8*, ...) @printf(i8* %fmt_ptr, i32 %val)
  ret void
}

"""

    def __get_variable_register(self, variable: str) -> str:
        if variable not in self.variable_versions:
            self.variable_versions[variable] = 0
            return f"%{variable}"
        else:
            self.variable_versions[variable] += 1
            return f"%{variable}.{self.variable_versions[variable]}"

    def __get_current_register(self, variable: str) -> str:
        if variable not in self.variable_versions or self.variable_versions[variable] == 0:
            return f"%{variable}"
        return f"%{variable}.{self.variable_versions[variable]}"
    

    def __get_current_token(self) -> Token:
        return self.tokens[self.current_token_index] if self.current_token_index < len(self.tokens) else self.tokens[-1]

    def __peek_token(self, offset: int = 1) -> Token:
        index = self.current_token_index + offset
        return self.tokens[index] if index < len(self.tokens) else self.tokens[-1]

    def __consume_token(self) -> Token:
        token = self.__get_current_token()
        if self.current_token_index < len(self.tokens) - 1:
            self.current_token_index += 1
        return token

    def __expect_token(self, token_type: TokenType) -> Token:
        token = self.__get_current_token()
        if token.token_type != token_type:
            raise ValueError(
                f"I expected a token of the type {token_type.name} but you gave me {token.token_type.name} "
                f"at line {token.line} and index {token.index}")
        return self.__consume_token()

    def __validate_variable_initialized(self, variable: str, line: int) -> None:
        if variable not in self.initialized_variables:
            raise ValueError(
                f"Why did you decide that you are permitted to use uninitialized variables??? "
                f"You placed uninitialized '{variable}' at line {line}!!!"
            )

    def __generate_assignment_ir(self, variable: str, value: str) -> str:
        reg = self.__get_variable_register(variable)
        return f"  {reg} = add i32 0, {value}"

    def __generate_operation_ir(self, variable: str, operator: str, operand1: str, operand2: str) -> str:
        reg = self.__get_variable_register(variable)
        return f"  {reg} = {Compiler.llvm_ir_operators.get(operator)} i32 {operand1}, {operand2}"

    def __generate_return_ir(self, value: str) -> str:
        return f"  call void @printResult(i32 {value})\n  ret i32 {value}"

    def __parse_value_or_expression(self, variable: str, is_initialization: bool = False) -> str:
        token = self.__get_current_token()

        if token.token_type == TokenType.NUMBER:
            return self.__parse_number_value_or_expression(variable, is_initialization)
        
        if token.token_type == TokenType.VARIABLE:
            return self.__parse_variable_value_or_expression(variable, is_initialization)
        
        operand1, operator, operand2 = self.__parse_expression(variable, is_initialization)
        return self.__generate_operation_ir(variable, operator, operand1, operand2)

    def __parse_number_value_or_expression(self, variable: str, is_initialization: bool) -> str:
        token = self.__get_current_token()
        next_token = self.__peek_token()
        
        if next_token.token_type in [TokenType.PLUS, TokenType.MINUS, TokenType.MULTIPLY]:
            operand1, operator, operand2 = self.__parse_expression(variable, is_initialization)
            return self.__generate_operation_ir(variable, operator, operand1, operand2)
        else:
            value = token.value
            self.__consume_token()
            return self.__generate_assignment_ir(variable, value)

    def __parse_variable_value_or_expression(self, variable: str, is_initialization: bool) -> str:
        token = self.__get_current_token()
        variable_name = token.value
        
        self.__check_self_assignment(variable, variable_name, is_initialization, token.line)
        
        next_token = self.__peek_token()
        if next_token.token_type in [TokenType.PLUS, TokenType.MINUS, TokenType.MULTIPLY]:
            operand1, operator, operand2 = self.__parse_expression(variable, is_initialization)
            return self.__generate_operation_ir(variable, operator, operand1, operand2)
        else:
            self.__validate_variable_initialized(variable_name, token.line)
            self.__consume_token()
            return self.__generate_assignment_ir(variable, self.__get_current_register(variable_name))

    def __check_self_assignment(self, target: str, source: str, is_initialization: bool, line: int) -> None:
        if source == target:
            if is_initialization:
                raise ValueError(f"Self-assignment like '{target} = {target}' is not allowed at line {line}!")
            next_token = self.__peek_token()
            if next_token.token_type not in [TokenType.PLUS, TokenType.MINUS, TokenType.MULTIPLY]:
                raise ValueError(f"Self-assignment like '{target} = {target}' is not allowed at line {line}!")

    def __parse_variable_declaration(self) -> str:
        type_info = self.__parse_type_and_mutability()
        variable_info = self.__parse_variable_name()
        
        if variable_info['name'] in self.declared_variables:
            raise ValueError(f"Variable '{variable_info['name']}' has already been declared at line {variable_info['line']}")
        
        self.declared_variables[variable_info['name']] = type_info['mutable']
        
        self.__expect_token(TokenType.LEFT_BRACKET)
        llvm_code = self.__parse_value_or_expression(variable_info['name'], is_initialization=True)
        self.__expect_token(TokenType.RIGHT_BRACKET)
        
        self.initialized_variables.add(variable_info['name'])
        return llvm_code

    def __parse_type_and_mutability(self) -> dict:
        self.__expect_token(TokenType.I32_TYPE)
        can_mutate = False
        
        if self.__get_current_token().token_type == TokenType.MUT:
            can_mutate = True
            self.__consume_token()
        
        return {'mutable': can_mutate}

    def __parse_variable_name(self) -> dict:
        token_variable = self.__expect_token(TokenType.VARIABLE)
        return {'name': token_variable.value, 'line': token_variable.line}

    def __parse_expression(self, target_variable: str = None, is_initialization: bool = False) -> tuple[str, str, str]:
        operand1 = self.__configure_operand_in_expression(target_variable, is_initialization)
        operator = self.__configure_operator_in_expression()
        operand2 = self.__configure_operand_in_expression(target_variable, is_initialization)
        return operand1, operator, operand2

    def __configure_operator_in_expression(self) -> str:
        operator_token = self.__get_current_token()
        if operator_token.token_type not in [TokenType.PLUS, TokenType.MINUS, TokenType.MULTIPLY]:
            raise ValueError(
                f"You should have used one of {', '.join(Compiler.llvm_ir_operators.keys())} "
                f"operators at line {operator_token.line}"
            )
        operator = operator_token.value
        self.__consume_token()
        return operator

    def __configure_operand_in_expression(self, target_variable: str = None, is_initialization: bool = False) -> str:
        operand_token = self.__get_current_token()
        if operand_token.token_type not in [TokenType.NUMBER, TokenType.VARIABLE]:
            raise ValueError(
                f"You should have used either a number or a variable "
                f"at line {operand_token.line}, not {operand_token.value}!"
            )

        if is_initialization and operand_token.token_type == TokenType.VARIABLE and operand_token.value == target_variable:
            raise ValueError(
                f"Self-assignment is not allowed in case of the first initialisation! "
                f"You tried to use '{target_variable}' at line {operand_token.line}"
            )

        operand = self.__resolve_operand(operand_token.value, operand_token.line)
        self.__consume_token()
        return operand

    def __parse_assignment(self) -> str:
        variable_token = self.__expect_token(TokenType.VARIABLE)
        variable = variable_token.value

        if variable not in self.declared_variables:
            raise ValueError(
                f"Variable '{variable}' at line {variable_token.line} is not declared, bro!"
            )

        if not self.declared_variables[variable]:
            raise ValueError(
                f"Sorry, but you cannot assign something new to an immutable "
                f"variable!!! Remove '{variable}' from line {variable_token.line}!"
            )

        self.__expect_token(TokenType.ASSIGNMENT)
        return self.__parse_value_or_expression(variable, is_initialization=False)

    def __resolve_operand(self, operand: str, line: int) -> str:
        if operand.lstrip('-').isdigit():
            return operand

        if operand in self.initialized_variables:
            return self.__get_current_register(operand)

        raise ValueError(f"I spotted uninitialized operand '{operand}' at line {line}!")

    def __parse_return(self) -> str:
        self.__expect_token(TokenType.RETURN)
        token = self.__get_current_token()

        if token.token_type == TokenType.NUMBER:
            value = token.value
            self.__consume_token()
            return self.__generate_return_ir(value)

        if token.token_type == TokenType.VARIABLE:
            variable_name = token.value
            self.__validate_variable_initialized(variable_name, token.line)
            self.__consume_token()
            return self.__generate_return_ir(self.__get_current_register(variable_name))

        raise ValueError(
            f"You should have used either a number or a variable "
            f"at line {token.line}, not {token.value}!"
        )

    def parse_tokens(self) -> str:
        self.translated_lines.append("define i32 @main() {")
        has_return = False

        while not self.__get_current_token().token_type == TokenType.THE_END:
            token = self.__get_current_token()
            match token.token_type:
                case TokenType.COMMENT:
                    self.__consume_token()
                    continue
                case TokenType.I32_TYPE:
                    result = self.__parse_variable_declaration()
                    self.translated_lines.append(result)
                case TokenType.VARIABLE:
                    result = self.__parse_assignment()
                    self.translated_lines.append(result)
                case TokenType.RETURN:
                    result = self.__parse_return()
                    self.translated_lines.append(result)
                    has_return = True
                    break
                case _:
                    raise ValueError(f"I did not expect to see a token {token.token_type.name} at line {token.line}")

        if not has_return:
            self.translated_lines.append("  call void @printResult(i32 0)")
            self.translated_lines.append("  ret i32 0")

        self.translated_lines.append("}")
        return "\n".join(self.translated_lines)


def parse_arguments() -> tuple[str, str]:
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help="Input file that contains source code")
    parser.add_argument('output_file', help="Output LLVM IR file")
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"File '{args.input_file}' was not found!")
        sys.exit(1)

    return args.input_file, args.output_file


def get_file_content(file_name: str) -> str:
    with open(file_name, 'r') as file:
        return file.read()


def run_program():
    try:
        input_file, output_file = parse_arguments()
        source_code = get_file_content(input_file)

        lexer = Lexer(source_code)
        tokens = lexer.tokenize()

        compiler = Compiler(tokens)
        converted_code = compiler.parse_tokens()

        with open(output_file, "w") as file:
            file.write(Compiler.get_print_function_llvm())
            file.write(converted_code)

        print(f"Successfully compiled '{input_file}' to '{output_file}'")
        sys.exit(0)

    except ValueError as e:
        print(f"OHHHH NOOOO, compilation failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error :((((: {e}")
        sys.exit(1)


run_program()