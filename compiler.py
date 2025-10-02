#!/usr/bin/env python3
import os.path
import sys
import argparse
import re


class Compiler:

    llvm_ir_operands = {
        "+": "add",
        "-": "sub",
        "*": "mul"
    }

    def __init__(self):
        self.translated_lines = []
        self.declared_variables = dict()

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

    def __parse_variable_declaration(self, line: str):
        line_parts = line.split()
        if len(line_parts) != 2:
            raise ValueError("Declaration of variables must look like this: var x")
        variable = line_parts[1].strip()
        if variable in self.declared_variables:
            raise ValueError(f"The variable {variable} has been already declared!")
        elif variable.isalnum() and not variable[0].isdigit():
            self.declared_variables[variable] = False
        else:
            raise ValueError(f"Incorrect variable name: {variable}. Must be alphanumeric and start with a letter.")

    def __parse_assignment(self, line: str) -> str:
        if line.count("=") != 1 or line.startswith("=") or line.endswith("="):
            raise ValueError("Incorrect usage of '='! Assignment cannot be defined!!!")

        variable, expression = line.split('=', 1)
        variable = variable.strip()
        expression = expression.strip()

        if variable not in self.declared_variables.keys():
            raise ValueError(f"The variable {variable} was not declared!")

        expression = expression.strip()
        
        if (expression.isdigit() or (expression.lstrip("-").isdigit())):
            self.declared_variables[variable] = True
            return f"  %{variable} = add i32 0, {expression}"
        elif expression in self.declared_variables:
            if not self.declared_variables[expression]:
                raise ValueError(f"Variable {expression} is not initialized!")
            if expression == variable:
                raise ValueError("Self-assignment is not allowed here!")
            self.declared_variables[variable] = True
            return f"  %{variable} = add i32 0, %{expression}"  
        else:
            return f"  %{variable} = {self.__parse_expression(variable, expression)}"

    def __parse_expression(self, variable, expression: str) -> str:
        pattern = r'(?<=[a-zA-Z0-9])\s*([+\-*])\s*'
        parts = re.split(pattern, expression)
        
        parts = [p.strip() for p in parts if p.strip()]
        
        if len(parts) != 3:
            raise ValueError("Your expression must be simple, only 2 operands are allowed!")

        operand_1, operation, operand_2 = parts
        operation = operation.strip()
        operand_1 = operand_1.strip()
        operand_2 = operand_2.strip()

        if not self.declared_variables[variable]:
            if operand_1 == variable or operand_2 == variable:
                raise ValueError("Self-assignment is not allowed in case of the first initialisation!")

        if operation not in Compiler.llvm_ir_operands:
            raise ValueError(
                f"Operation {operation} is not allowed. Allowed: {', '.join(Compiler.llvm_ir_operands.keys())}")

        operand_1 = self.__resolve_operand(operand_1)
        operand_2 = self.__resolve_operand(operand_2)

        self.declared_variables[variable] = True
        return f"{Compiler.llvm_ir_operands.get(operation)} i32 {operand_1}, {operand_2}"

    def __resolve_operand(self, operand: str) -> str:
        if operand in self.declared_variables and self.declared_variables[operand]:
            return f"%{operand}"
        elif operand.isdigit() or operand.lstrip('-').isdigit():
            return operand
        raise ValueError("Operands must be either i32 integers or both declared and initialized variables!")

    def __parse_return(self, line: str) -> str:
        line_parts = line.split()
        if len(line_parts) != 2:
            raise ValueError("After 'return' keyword you must specify a single return value!")
        value = line_parts[1].strip()
        if value.lstrip('-').isdigit():
            return f"  call void @printResult(i32 {value})\n  ret i32 {value}"
        elif value in self.declared_variables and self.declared_variables[value]:
            return f"  call void @printResult(i32 %{value})\n  ret i32 %{value}"
        raise ValueError("""The value after the 'return' keyword must 
                            be either a previously declared and initialized variable or a number""")

    def __parse_input_file_line(self, line: str) -> str:
        if line.startswith("var "):
            self.__parse_variable_declaration(line)
        elif line.startswith("return "):
            return self.__parse_return(line)
        else:
            return self.__parse_assignment(line)
        return ""

    def parse_input_file(self, input_file: str) -> str:
        with open(input_file, 'r') as file:
            lines = file.readlines()

        self.translated_lines.append("define i32 @main() {")

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            else:
                result = self.__parse_input_file_line(line)
                if result:
                    self.translated_lines.append(result)

        self.translated_lines.append("}")

        return "\n".join(self.translated_lines)


def get_input_file() -> str:
    this_filename = os.path.basename(__file__)
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help="Input file that contains code with a txt extension")
    args = parser.parse_args()
    input_file = args.input_file

    if not os.path.exists(input_file):
        print(f"File '{input_file}' was not found! Usage: python {this_filename} <input_file>")
        sys.exit(1)

    return input_file


def run_program():
    compiler = Compiler()
    input_file = get_input_file()

    try:
        converted_code = compiler.parse_input_file(input_file)
        output_file = os.path.splitext(input_file)[0] + ".ll"
        with open(output_file, "w") as file:
            file.write(Compiler.get_print_function_llvm())
            file.write(converted_code)
        print(f"Successfully compiled '{input_file}' to '{output_file}'")
    except ValueError as e:
        print(f"Compilation failed: {e}")
        sys.exit(1)

    sys.exit(0)


run_program()