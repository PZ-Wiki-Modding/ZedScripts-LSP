from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Iterator, TypeVar, Generic

from ..enums.Diagnostic import DiagnosticType
from ..providers.diagnostics import DiagnosticCollection
from ..structure.lexer import TextRange

if TYPE_CHECKING:
    from .ast import ValueNode, BlockNode, Chunk
    from ..scripts.dataset import Dataset

NodeT = TypeVar("NodeT")


class Element(Generic[NodeT]):
    def __init__(self) -> None:
        super().__init__()
        self.node: NodeT
        """AST node of the element."""


class Value(Element["ValueNode"]):
    def __init__(self, string: str, node: ValueNode, comment: str) -> None:
        super().__init__()
        self.string: str = string
        """
        Includes any whitespace preceding the value, including before any preceding comments.
        This sucks, but it's how the game parses them, so potentially needed for 1:1 behaviour.
        """
        self.node: ValueNode = node
        self.comment: str = comment

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

    def validate(self, dataset: Dataset, diagnostics: DiagnosticCollection) -> bool:
        #TODO: to implement
        return True


class Block:
    def __init__(self, type: str):
        self.type: str = type
        """
        Type of the block.
        All blocks must have an explicit type, except the root block of a file, which is given an empty string.
        If the block was created from AST, the type may be empty for non-root blocks, but this is ill-formed.
        """
        self.children: list[ScriptBlock] = []
        self.values: list[Value] = []

    def __iter__(self) -> Iterator[ScriptBlock]:
        return iter(self.children)

    def validate(self, dataset: Dataset, diagnostics: DiagnosticCollection) -> bool: ...
    def validate_block(self, dataset: Dataset, diagnostics: DiagnosticCollection) -> bool: ...
    def validate_children(self, dataset: Dataset, diagnostics: DiagnosticCollection): ...



class ScriptBlock(Block, Element["BlockNode"]):
    def __init__(self, type: str, id: str, node: BlockNode, parent: Block, comment: str) -> None:
        super().__init__(type)
        self.id: str = id
        """
        ID of the block.
        Blocks are not required to have an ID: this is represented by the empty string.
        """

        self.node = node
        self.comment: str = comment

        self.parent = parent

    def __repr__(self) -> str:
        if self.id == "":
            return "<" + self.type + ">"
        else:
            return "<" + self.type + " " + self.id + ">"

    def validate(self, dataset: Dataset, diagnostics: DiagnosticCollection) -> bool:
        # validate self
        if not self.validate_block(dataset, diagnostics):
            return False

        # validate key-values
        for value in self.values:
            value.validate(dataset, diagnostics)

        # validate children
        self.validate_children(dataset, diagnostics)
        
        return True

    def validate_block(self, dataset: Dataset, diagnostics: DiagnosticCollection) -> bool:
        node = self.node
        if node.type is None:
            return False

        # validate the type of the block
        type = self.type
        if not dataset.is_script_block(type):
            diagnostics.add(
                DiagnosticType.SCHEMA_UNEXPECTED_BLOCK,
                node.type.to_range(),
                {"type": type}
            )
            logging.debug("Unexpected block type: %s", type)
            return False

        return True

    def validate_children(self, dataset: Dataset, diagnostics: DiagnosticCollection):
        # validate all children blocks
        for child in self.children:
            child.validate(dataset, diagnostics)


class Root(Block, Element["Chunk"]):
    def __init__(self, type: str, node: Chunk, comment: str) -> None:
        super().__init__(type)
        self.type = type
        self.node = node
        self.comment = comment

    def validate_block(self, dataset: Dataset, diagnostics: DiagnosticCollection) -> bool:
        """Root block is always considered valid."""
        return True