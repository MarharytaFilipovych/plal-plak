#!/usr/bin/env python3
from .node.program_node import ProgramNode
from .node.assign_node import AssignNode
from .node.binary_op_node import BinaryOpNode
from .node.decl_node import DeclNode
from .node.expr_node import ExprNode
from .node.id_node import IDNode
from .node.number_node import NumberNode
from .node.return_node import ReturnNode


class CodeGenerator:
    def __init__(self):
        self.variable_versions: dict[str, int] = {}
        self.translated_lines: list[str] = []

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

    def generate(self, ast: ProgramNode) -> str:
        self.translated_lines = []
        self.__generate_program(ast)

        return "\n".join([
            self.get_print_function_llvm(),
            "define i32 @main() {",
            *self.translated_lines,
            "}"
        ])

    def __generate_program(self, node: ProgramNode):
        for statement in node.statement_nodes:
            if isinstance(statement, DeclNode):
                self.__generate_declaration(statement)
            elif isinstance(statement, AssignNode):
                self.__generate_assignment(statement)

        self.__generate_return(node.return_node)

    def __generate_declaration(self, node: DeclNode):
        value = self.__generate_expression(node.expr_node)
        reg = self.__get_variable_register(node.variable)
        self.translated_lines.append(f"  {reg} = add i32 0, {value}")

    def __generate_assignment(self, node: AssignNode):
        value = self.__generate_expression(node.expr_node)
        reg = self.__get_variable_register(node.variable)
        self.translated_lines.append(f"  {reg} = add i32 0, {value}")

    def __generate_return(self, node: ReturnNode):
        value = self.__generate_expression(node.expr_node)
        self.translated_lines.append(f"  call void @printResult(i32 {value})")
        self.translated_lines.append(f"  ret i32 {value}")

    def __generate_expression(self, node: ExprNode) -> str:
        match node:
            case NumberNode():
                return str(node.value)
            case IDNode():
                return self.__get_current_register(node.value)
            case BinaryOpNode():
                return self.__generate_binary_op(node)
            case _:
                raise ValueError(f"Unsupported expression type: {type(node)}")

    def __generate_binary_op(self, node: BinaryOpNode) -> str:
        left_value = self.__generate_expression(node.left)
        right_value = self.__generate_expression(node.right)

        temp_reg = self.__get_variable_register(f"_temp_{id(node)}")
        llvm_op = node.operator.to_llvm()

        self.translated_lines.append(
            f"  {temp_reg} = {llvm_op} i32 {left_value}, {right_value}")

        return temp_reg

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
