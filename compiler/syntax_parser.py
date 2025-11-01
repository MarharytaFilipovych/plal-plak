#!/usr/bin/env python3
from typing import Union, Optional

from compiler.node.assign_node import AssignNode
from compiler.node.binary_op_node import BinaryOpNode
from compiler.node.code_block_node import CodeBlockNode
from compiler.node.decl_node import DeclNode
from compiler.node.expr_node import ExprNode
from compiler.node.factor_node import FactorNode
from compiler.node.function_decl_node import FunctionDeclNode, FunctionParam
from compiler.node.function_call_node import FunctionCallNode
from compiler.node.id_node import IDNode
from compiler.node.if_node import IfNode
from compiler.node.number_node import NumberNode
from compiler.node.program_node import ProgramNode
from compiler.node.return_node import ReturnNode
from compiler.node.stmt_node import StmtNode
from compiler.llvm_specifics.data_type import DataType
from compiler.llvm_specifics.operator import Operator
from compiler.node.bool_node import BooleanNode
from compiler.helpers.struct_field import StructField
from compiler.node.struct_decl_node import StructDeclNode
from compiler.node.struct_field_assign_node import StructFieldAssignNode
from compiler.node.struct_field_node import StructFieldNode
from compiler.node.struct_init_node import StructInitNode
from compiler.node.unary_op_node import UnaryOpNode
from compiler.token.token_type import TokenType
from compiler.token.token_class import Token
from compiler.constants import NOT

class SyntaxParser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current_token_index = 0
        self.next_scope_id = 1
        self.declared_structs: set[str] = set()

    def __peek(self) -> Token:
        return self.tokens[self.current_token_index] if self.current_token_index < len(self.tokens) else None

    def __eat(self) -> Token:
        token = self.__peek()
        if token:
            self.current_token_index += 1
        return token

    def __expect_token(self, token_type: TokenType) -> Token:
        token = self.__peek()
        if not token:
            raise ValueError(f"I expected a token of the type {token_type.name} but you decided to abandon this promising code!")

        if token.token_type != token_type:
            raise ValueError(f"I expected a token of the type {token_type.name} but you gave me '{token.value}' "
                            f"at line {token.line}!!!")

        return self.__eat()

    def parse_program(self) -> ProgramNode:
        self.__skip_newlines()

        struct_declarations = self.__parse_declaration_block(TokenType.STRUCT, self.__parse_struct_declaration)
        func_declarations = self.__parse_declaration_block(TokenType.FN, self.__parse_function_declaration)

        statements = self.__parse_statements()
        return_statement = self.__parse_program_return()
        self.__check_program_end()

        return ProgramNode(struct_declarations, func_declarations, statements, return_statement)

    def __parse_declaration_block(self, start_token_type, function):
        decls = []
        while self.__peek() and self.__peek().token_type == start_token_type:
            decls.append(function())
            self.__consume_newline_and_skip()
        return decls

    def __parse_statements(self) -> list[StmtNode]:
        statements = []

        while True:
            token = self.__peek()

            if not token or token.token_type == TokenType.THE_END:
                raise ValueError('Program must end with a "return" statement!')

            if token.token_type == TokenType.RETURN:
                break

            statement = self.__parse_statement()
            statements.append(statement)
            self.__consume_newline_and_skip()

        return statements

    def __parse_program_return(self) -> ReturnNode:
        return_statement = self.__parse_return()
        self.__skip_newlines()
        return return_statement

    def __check_program_end(self):
        if self.__peek() and self.__peek().token_type != TokenType.THE_END:
            raise ValueError(
                f"I did not want you to place this awful content "
                f"after the return statement at line {self.__peek().line}")

    def __parse_statement(self) -> StmtNode:
        token = self.__peek()

        if not token:
            raise ValueError("Why did you decide to abandon your work?! I want a statement!")

        if token.token_type == TokenType.STRUCT:
            return self.__parse_struct_declaration()
        elif TokenType.is_data_type(token.token_type):
            return self.__parse_variable_declaration()
        elif token.token_type == TokenType.VARIABLE:
            if self.__is_struct_type():
                return self.__parse_variable_declaration()
            return self.__parse_assignment()
        elif token.token_type == TokenType.IF:
            return self.__parse_if_statement()
        else:
            raise ValueError(f"You should have either declared a variable or assign this cutie to sth at line {token.line}, "
                            f"but you decided to use this token type: {token.value}")

    def __skip_newlines(self):
        while self.__peek() and self.__peek().token_type == TokenType.NEWLINE:
            self.__eat()

    def __expect_newline_or_end(self):
        token = self.__peek()
        if token and token.token_type not in [TokenType.NEWLINE, TokenType.THE_END]:
            raise ValueError(
                f"Each instruction must be on its own line! "
                f"You were expected to place a newline after the"
                f" instruction at line {token.line}, but you placed this: {token.value}")
        if token and token.token_type == TokenType.NEWLINE:
            self.__eat()

    def __consume_newline_and_skip(self):
        self.__expect_newline_or_end()
        self.__skip_newlines()

    def __is_struct_type(self) -> bool:
        token = self.__peek()
        return token and token.token_type == TokenType.VARIABLE and token.value in self.declared_structs

    def __parse_variable_declaration(self) -> DeclNode:
        var_type = self.__parse_type()
        can_mutate = self.__parse_mutability()
        token_variable = self.__expect_token(TokenType.VARIABLE)
        
        # Check if this is a struct type initialization (multiple values in braces)
        if var_type in self.declared_structs:
            init_expr = self.__parse_struct_initialization(var_type, token_variable.line)
        else:
            init_expr = self.__parse_initializer()

        data_type = DataType.from_string(var_type) if var_type in ["i32", "i64", "bool"] else var_type
        return DeclNode(token_variable.value, init_expr, token_variable.line, can_mutate, data_type)

    def __parse_struct_declaration(self) -> StructDeclNode:
        self.__expect_token(TokenType.STRUCT)
        struct_token = self.__expect_token(TokenType.VARIABLE)
        struct_name = struct_token.value

        if struct_name in self.declared_structs:
            raise ValueError(f"The struct {struct_name} was already declared, you dummy!")

        self.declared_structs.add(struct_name)
        self.__consume_newline_and_skip()
        self.__expect_token(TokenType.LEFT_BRACKET)
        self.__consume_newline_and_skip()

        fields = self.__parse_struct_fields()

        self.__expect_token(TokenType.RIGHT_BRACKET)
        return StructDeclNode(struct_name, fields, struct_token.line)

    def __parse_struct_fields(self) -> list[StructField]:
        fields: list[StructField] = []
        while self.__peek() and self.__peek().token_type != TokenType.RIGHT_BRACKET:
            var_type = self.__parse_type()
            can_mutate = self.__parse_mutability()
            token_variable = self.__expect_token(TokenType.VARIABLE)
            fields.append(StructField(var_type, token_variable.value, can_mutate))
            self.__consume_newline_and_skip()
        return fields

    def __parse_struct_initialization(self, struct_type: str, line: int) -> StructInitNode:
        self.__expect_token(TokenType.LEFT_BRACKET)
        init_exprs: list[ExprNode] = []

        if self.__peek() and self.__peek().token_type != TokenType.RIGHT_BRACKET:
            init_exprs.append(self.__parse_expression())

            while self.__peek() and self.__peek().token_type == TokenType.COMMA:
                self.__expect_token(TokenType.COMMA)
                init_exprs.append(self.__parse_expression())

        self.__expect_token(TokenType.RIGHT_BRACKET)
        return StructInitNode(struct_type, init_exprs, line)

    def __parse_type(self) -> str:
        token = self.__peek()

        if (TokenType.is_data_type(token.token_type)) or \
                (token.token_type == TokenType.VARIABLE and token.value in self.declared_structs):
            self.__eat()
            return token.value
        raise ValueError(
            f"I expected some type declaration at line {token.line} but I cannot recognize this type: {token.value}!")

    def __parse_mutability(self) -> bool:
        if self.__peek() and self.__peek().token_type == TokenType.MUT:
            self.__eat()
            return True
        return False

    def __parse_initializer(self) -> ExprNode:
        self.__expect_token(TokenType.LEFT_BRACKET)
        init_expr = self.__parse_expression()
        self.__expect_token(TokenType.RIGHT_BRACKET)
        return init_expr

    def __parse_assignment(self) -> AssignNode:
        variable_token = self.__expect_token(TokenType.VARIABLE)
        field_chain = self.__gather_field_accessors(variable_token.value) if self.__is_field_access() else None

        self.__expect_token(TokenType.ASSIGNMENT)
        value_expr = self.__parse_expression()

        return (
            StructFieldAssignNode(StructFieldNode(field_chain, variable_token.line), value_expr, variable_token.line)
            if field_chain else AssignNode(variable_token.value, value_expr, variable_token.line))

    def __parse_if_statement(self) -> IfNode:
        if_token = self.__expect_token(TokenType.IF)
        condition = self.__parse_expression()
        self.__consume_newline_and_skip()

        then_block = self.__parse_code_block()
        else_block = self.__try_parse_else_block()

        return IfNode(condition, then_block, else_block, if_token.line)

    def __try_parse_else_block(self) -> Optional[CodeBlockNode]:
        token = self.__peek()

        if not token or token.token_type != TokenType.NEWLINE:
            return None

        saved_index = self.current_token_index
        self.__eat()
        self.__skip_newlines()

        if self.__peek() and self.__peek().token_type == TokenType.ELSE:
            self.__eat()
            self.__consume_newline_and_skip()
            return self.__parse_code_block()
        else:
            self.current_token_index = saved_index
            return None

    def __parse_code_block(self) -> CodeBlockNode:
        self.__expect_token(TokenType.LEFT_BRACKET)
        self.__consume_newline_and_skip()

        statements, return_node = self.__parse_block_contents()

        self.__expect_token(TokenType.RIGHT_BRACKET)
        scope_id = self.next_scope_id
        self.next_scope_id += 1
        return CodeBlockNode(statements, return_node, scope_id)

    def __parse_block_contents(self) -> tuple[list[StmtNode], Optional[ReturnNode]]:
        statements = []
        return_node = None

        while True:
            token = self.__peek()

            if not token:
                raise ValueError("Code block must end with }!")

            if token.token_type == TokenType.RIGHT_BRACKET:
                break

            if token.token_type == TokenType.RETURN:
                return_node = self.__parse_return()
                self.__consume_newline_and_skip()
                self.__check_no_code_after_return()
                break

            statement = self.__parse_statement()
            statements.append(statement)
            self.__consume_newline_and_skip()

        return statements, return_node

    def __check_no_code_after_return(self):
        next_token = self.__peek()
        if next_token and next_token.token_type != TokenType.RIGHT_BRACKET:
            raise ValueError(f"Code after return statement is not allowed at line {next_token.line}!")

    def __parse_return(self) -> ReturnNode:
        self.__expect_token(TokenType.RETURN)
        return ReturnNode(self.__parse_expression())

    def __parse_expression(self) -> ExprNode:
        left_operand = self.__parse_factor()
        while True:
            token = self.__peek()
            if not token or not TokenType.is_operator(token.token_type):
                break
            operator_token = self.__eat()
            operator = Operator.from_string(operator_token.value)
            right_operator = self.__parse_factor()
            left_operand = BinaryOpNode(left_operand, operator, right_operator)
        return left_operand

    def __parse_factor(self) -> Union[FactorNode, UnaryOpNode]:
        token = self.__peek()

        if token and token.token_type == TokenType.NOT:
            self.__eat()
            operand = self.__parse_factor()
            return UnaryOpNode(NOT, operand)

        return self.__parse_primary()

    def __parse_primary(self) -> FactorNode:
        token = self.__peek()

        if not token:
            raise ValueError(f"You should have used either a number, a variable, or a boolean, "
                             f"but you decided to abandon your work!")

        match token.token_type:
            case TokenType.NUMBER:
                self.__eat()
                return NumberNode(token.value)
            case TokenType.VARIABLE:
                self.__eat()
                if self.__peek() and self.__peek().token_type == TokenType.LEFT_DUZHKA:
                    return self.__parse_function_call(token.value, token.line)

                if self.__is_field_access():
                    return StructFieldNode(self.__gather_field_accessors(token.value), token.line)

                if self.__is_struct_initialization(token.value):
                    return self.__parse_struct_initialization(token.value, token.line)

                return IDNode(token.value, token.line)
            case TokenType.TRUE | TokenType.FALSE:
                self.__eat()
                return BooleanNode(token.value)
            case _:
                raise ValueError(f"You should have used either a number, a variable, or a boolean "
                                 f"at line {token.line}, not {token.value}!")

    def __is_struct_initialization(self, value: str) -> bool:
        return self.__peek() and self.__peek().token_type == TokenType.LEFT_BRACKET and value in self.declared_structs

    def __is_field_access(self) -> bool:
        return self.__peek() and self.__peek().token_type == TokenType.DOT

    def __gather_field_accessors(self, base_variable: str) -> list[str]:
        field_chain = [base_variable]

        while self.__is_field_access():
            self.__expect_token(TokenType.DOT)
            field_token = self.__expect_token(TokenType.VARIABLE)
            field_chain.append(field_token.value)

        return field_chain

    def __parse_function_declaration(self) -> FunctionDeclNode:
        self.__expect_token(TokenType.FN)
        func_name_token = self.__expect_token(TokenType.VARIABLE)
        self.__expect_token(TokenType.ASSIGNMENT)

        params = self.__parse_parenthesized_list(self.__parse_function_param)

        self.__expect_token(TokenType.ARROW)
        return_type = self.__parse_type()
        self.__consume_newline_and_skip()
        body = self.__parse_code_block()

        return FunctionDeclNode(func_name_token.value, params, return_type, body, func_name_token.line)

    def __parse_function_param(self) -> FunctionParam:
        param_type = self.__parse_type()
        param_name = self.__expect_token(TokenType.VARIABLE).value
        return FunctionParam(param_type, param_name)

    def __parse_function_call(self, func_name: str, line: int) -> FunctionCallNode:
        arguments = self.__parse_parenthesized_list(self.__parse_expression)
        return FunctionCallNode(func_name, arguments, line)

    def __parse_parenthesized_list(self, parse_item_fn):
        self.__expect_token(TokenType.LEFT_DUZHKA)
        items = []

        if self.__peek().token_type != TokenType.RIGHT_DUZHKA:
            items.append(parse_item_fn())
            while self.__peek() and self.__peek().token_type == TokenType.COMMA:
                self.__eat()
                items.append(parse_item_fn())

        self.__expect_token(TokenType.RIGHT_DUZHKA)
        return items