#!/usr/bin/env python3
from .lexer_state import LexerState
from ..token.token_type import TokenType
from ..token.token_class import Token


class Lexer:
    WHITESPACE = ' \t\r'
    OPERATORS = '+-*='
    KEYWORDS: dict = {
        "i32": TokenType.I32_TYPE,
        "mut": TokenType.MUT,
        "return": TokenType.RETURN,
        "false": TokenType.FALSE,
        "true": TokenType.TRUE,
        "i64": TokenType.I64_TYPE,
        "bool": TokenType.BOOL,
        "if": TokenType.IF,
        "else": TokenType.ELSE
    }

    PREDEFINED_CHARS: dict = {
        '{': TokenType.LEFT_BRACKET,
        '}': TokenType.RIGHT_BRACKET,
        '+': TokenType.PLUS,
        '*': TokenType.MULTIPLY
    }

    def __init__(self, source: str):
        self.source = source
        self.current_position = 0
        self.line = 1
        self.index = 1
        self.tokens = []
        self.state = LexerState.INITIAL

        self.current_token_start = 0
        self.current_token_start_line = 1
        self.current_token_start_index = 1

    @staticmethod
    def __is_whitespace(char: str):
        return char is not None and char in Lexer.WHITESPACE

    @staticmethod
    def __is_operator(char: str):
        return char is not None and char in Lexer.OPERATORS

    def __add_token(self, token_type: TokenType, value: str, line: int = None, index: int = None):
        line = line if line is not None else self.line
        index = index if index is not None else self.index
        self.tokens.append(Token(token_type, value, line, index))

    def __check_for_and_get_next_char(self):
        return self.source[self.current_position + 1] if self.current_position + 1 < len(self.source) else None

    def __start_new_token(self, new_state: LexerState):
        self.state = new_state
        self.current_token_start = self.current_position
        self.current_token_start_line = self.line
        self.current_token_start_index = self.index
        self.__move_to_next_char()

    def __move_to_next_char(self):
        if self.current_position < len(self.source):
            if self.source[self.current_position] == '\n':
                self.line += 1
                self.index = 1
            else:
                self.index += 1
            self.current_position += 1

    def tokenize(self) -> list[Token]:
        while self.current_position < len(self.source):
            char = self.source[self.current_position]
            match self.state:
                case LexerState.INITIAL:
                    self.__manage_initial_state(char)
                case LexerState.VARIABLE:
                    self.__manage_identifier_state(char)
                case LexerState.NUMBER:
                    self.__manage_number_state(char)
                case LexerState.COMMENT:
                    self.__manage_comment_state(char)
        self.__build_current_token()
        self.tokens.append(Token(TokenType.THE_END, "", self.line, self.index))
        return self.tokens

    def __manage_initial_state(self, char):
        if char == '\n':
            self.__add_token(TokenType.NEWLINE, '\n')
            self.__move_to_next_char()
            return

        if self.__is_whitespace(char):
            self.__move_to_next_char()
            return

        if char in Lexer.PREDEFINED_CHARS:
            self.__add_token(Lexer.PREDEFINED_CHARS[char], char)
            self.__move_to_next_char()
            return

        if char == '-':
            next_char = self.__check_for_and_get_next_char()
            if next_char and next_char.isdigit():
                self.__start_new_token(LexerState.NUMBER)
            else:
                self.__add_token(TokenType.MINUS, '-')
                self.__move_to_next_char()
            return

        if char == '=':
            next_char = self.__check_for_and_get_next_char()
            if next_char == '=':
                self.__add_token(TokenType.EQUALS, '==')
                self.__move_to_next_char()
                self.__move_to_next_char()
            else:
                self.__add_token(TokenType.ASSIGNMENT, '=')
                self.__move_to_next_char()
            return

        if char == '!':
            next_char = self.__check_for_and_get_next_char()
            if next_char == '=':
                self.__add_token(TokenType.NOT_EQUALS, '!=')
                self.__move_to_next_char()
                self.__move_to_next_char()
            else:
                self.__add_token(TokenType.NOT, "!")
                self.__move_to_next_char()
            return

        if char.isalpha():
            self.__start_new_token(LexerState.VARIABLE)
            return

        if char.isdigit():
            self.__start_new_token(LexerState.NUMBER)
            return

        if char == '/' and self.__check_for_and_get_next_char() == '/':
            self.state = LexerState.COMMENT
            self.__move_to_next_char()
            self.__move_to_next_char()
            return

        raise ValueError(
            f"I did not expect character '{char}' to be "
            f"placed at line {self.line}, column {self.index}!!!"
        )

    def __manage_identifier_state(self, char: str):
        if char.isalnum():
            self.__move_to_next_char()
        else:
            self.__build_current_token()
            self.state = LexerState.INITIAL

    def __manage_number_state(self, char: str):
        if char.isdigit():
            self.__move_to_next_char()
        else:
            self.__build_current_token()
            self.state = LexerState.INITIAL

    def __manage_comment_state(self, char):
        if char == '\n' or char is None:
            self.state = LexerState.INITIAL
        self.__move_to_next_char()

    def __build_identifier_token(self, value: str):
        token_type = Lexer.KEYWORDS.get(value, TokenType.VARIABLE)
        self.__add_token(token_type, value, self.current_token_start_line, self.current_token_start_index)

    def __build_number_token(self, value: str):
        if not value.lstrip('-').isdigit():
            raise ValueError(
                f"Do you think that this is a correct number: '{value}'? It is not!!!"
                f"You placed that awful thing at line {self.current_token_start_line} "
                f"and column {self.current_token_start_index}."
            )
        self.__add_token(TokenType.NUMBER, value, self.current_token_start_line, self.current_token_start_index)

    def __build_current_token(self):
        if self.state == LexerState.INITIAL:
            return
        value = self.source[self.current_token_start:self.current_position]
        match self.state:
            case LexerState.VARIABLE:
                self.__build_identifier_token(value)
            case LexerState.NUMBER:
                self.__build_number_token(value)