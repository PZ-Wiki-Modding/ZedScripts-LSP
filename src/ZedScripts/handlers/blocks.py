from __future__ import annotations

import typing

from .lexer import TextPosition, TextRange, TokenType, TokenCollection

if typing.TYPE_CHECKING:
    from .lexer import Token
    from .ast import Node, BlockBody, ValueNode


class Element:
    def __init__(self) -> None:
        super().__init__()
        self.comment: str = ""
        self.node: Node | None = None
        """AST node of the element. None if the block was not created from AST."""


class Value(Element):
    def __init__(self, string: str) -> None:
        super().__init__()
        self.string: str = string
        """
        Includes any whitespace preceding the value, including before any preceding comments.
        This sucks, but it's how the game parses them, so potentially needed for 1:1 behaviour.
        """
        self.node: ValueNode | None = None

    def is_key_value(self) -> bool:
        return "=" in self.string

    def key(self) -> str:
        """
        Returns the stripped text before the first ``=`` in the value.
        Not all values take the form of key-value pairs.
        :return:
        """
        assert self.is_key_value()
        return self.string.split("=", 1)[0].strip()

    def value(self) -> str:
        """
        Returns the stripped text after the first ``=`` in the value.
        Not all values take the form of key-value pairs.
        :return:
        """
        if self.is_key_value():
            return self.string.split("=", 1)[1].strip()
        return self.string.strip()

    def __str__(self) -> str:
        return self.string


class Block(Element):
    def __init__(self, type: str) -> None:
        super().__init__()
        self.type: str = type
        """
        Type of the block.
        All blocks must have an explicit type, except the root block of a file, which is given an empty string.
        If the block was created from AST, the type may be empty for non-root blocks, but this is ill-formed.
        """
        self.id: str = ""
        """
        ID of the block.
        Blocks are not required to have an ID: this is represented by the empty string.
        """
        self.elements: list[Element] = []
        self.node: BlockBody | None = None

    def get_value(self, key: str) -> str | None:
        for value in self.values():
            if value.key() == key:
                return value.value()
        return None

    def get_block(self, type: str) -> Block | None:
        for block in self.blocks():
            if block.type == type:
                return block
        return None

    def values(self) -> list[Value]:
        values: list[Value] = []
        for element in self.elements:
            if isinstance(element, Value):
                values.append(element)
        return values

    def blocks(self) -> list[Block]:
        blocks: list[Block] = []
        for element in self.elements:
            if isinstance(element, Block):
                blocks.append(element)
        return blocks

    # def set_value(self, key: str, value: str) -> None:
    #     value_string = key + " = " + value
    #     for value in self.values:
    #         if value.key() == key:
    #             value.string = value_string
    #             # empty tokens list if it isn't already, as it's no longer accurate
    #             if len(value.tokens) > 0:
    #                 value.tokens = []
    #     self.values.append(
    #         Value(value_string)
    #     )

    def __repr__(self) -> str:
        if self.id == "":
            return "<" + self.type + ">"
        else:
            return "<" + self.type + " " + self.id + ">"
