from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from .lexer import Token
    from .ast import Node, BlockBody, ValueNode


NodeT = typing.TypeVar("NodeT")


class Element(typing.Generic[NodeT]):
    def __init__(self) -> None:
        super().__init__()
        self.comment: str = ""
        self.node: NodeT | None = None
        """AST node of the element. None if the block was not created from AST."""


class Value(Element["ValueNode"]):
    def __init__(self, string: str) -> None:
        super().__init__()
        self.string: str = string
        """
        Includes any whitespace preceding the value, including before any preceding comments.
        This sucks, but it's how the game parses them, so potentially needed for 1:1 behaviour.
        """

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


class Block(Element["BlockBody"]):
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

        self.parent: Block | None = None
        self.children: list[Block] = []
        self.values: list[Value] = []

    def __repr__(self) -> str:
        if self.id == "":
            return "<" + self.type + ">"
        else:
            return "<" + self.type + " " + self.id + ">"
