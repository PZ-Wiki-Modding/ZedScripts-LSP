from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Iterator, TypeVar, Generic

from ..enums.Diagnostic import DiagnosticType
from ..structure.lexer import TextRange
from ..providers.semantic_tokens import SemanticTokenType

if TYPE_CHECKING:
    from .ast import ValueNode, BlockNode, Chunk
    from ..scripts.dataset import Dataset
    from ..environment.document import Document

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

    def validate(self, dataset: Dataset) -> bool:
        #TODO: to implement
        return True


class Block:
    def __init__(self, document: 'Document', type: str):
        self.document: 'Document' = document
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

    def validate(self, dataset: Dataset) -> bool: ...
    def validate_block(self, dataset: Dataset) -> bool: ...
    def validate_children(self, dataset: Dataset): ...



class ScriptBlock(Block, Element["BlockNode"]):
    def __init__(self, document: 'Document',
                 type: str, id: str | None, 
                 node: BlockNode, parent: Block, 
                 comment: str) -> None:
        super().__init__(document=document, type=type)
        self.id: str | None = id
        """
        ID of the block.
        Blocks are not required to have an ID: this is represented by None.
        """

        self.node = node
        self.comment: str = comment

        self.parent = parent

    def __repr__(self) -> str:
        if self.id is None:
            return "<" + self.type + ">"
        else:
            return "<" + self.type + " " + self.id + ">"


# validation

    def add_diagnostic(self, type: DiagnosticType, location: TextRange, args: dict[str, Any] = {}) -> None:
        self.document.diagnostics.add(type=type, location=location, args=args)

    def add_semantic_token(self, type: SemanticTokenType, location: TextRange) -> None:
        self.document.semantic_tokens.add(type=type, location=location)


    def validate(self, dataset: Dataset) -> bool:
        # validate self
        if not self.validate_block(dataset):
            return False

        # validate key-values
        for value in self.values:
            value.validate(dataset)

        # validate children
        self.validate_children(dataset)
        
        return True

    def validate_block(self, dataset: Dataset) -> bool:
        """
        Validate the block itself, without considering its children or key-values.
        This includes:
        - validating the block type
        - validating its ID

        Args:
            dataset (Dataset): The dataset used for validation.
            diagnostics (DiagnosticCollection): The collection to which any validation diagnostics should be added.

        Returns:
            bool: True if the block is valid, False otherwise.
        """
        type = self.type
        node = self.node
        if node.type is None or type == "":
            return False
        
        self.add_semantic_token(
            SemanticTokenType.KEYWORD,
            node.type.to_range()
        )

        # validate the type of the block
        if not dataset.is_script_block(type):
            self.add_diagnostic(
                DiagnosticType.SCHEMA_UNKNOWN_BLOCK,
                node.type.to_range(),
                {"type": type}
            )
            logging.debug("Unexpected block type: %s", type)
            return False

        # validate the ID of the block
        if not self.validate_id(dataset):
            return False

        return True

    def validate_id(self, dataset: Dataset) -> bool:
        node = self.node
        blockData = dataset.get_script_block_data(self.type)
        idInfo = blockData.get('ID')

        # retrieve ID info
        id = self.id
        hasID = id is not None

        # no ID data means there shouldn't be any ID
        if hasID:
            node_id = node.id
            assert node_id is not None, "ID node should not be None when ID is present"

            # add semantic token for the ID
            # that the ID is valid or not
            self.add_semantic_token(
                SemanticTokenType.LABEL,
                node_id.to_range()
            )

            # there shouldn't be an ID
            if idInfo is None:
                self.add_diagnostic(
                    DiagnosticType.SCHEMA_UNEXPECTED_ID,
                    node_id.to_range(),
                    {"id": id}
                )
                logging.debug("Unexpected ID for block type %s: %s", self.type, id)
                return False

        return True


    def validate_children(self, dataset: Dataset):
        # validate all children blocks
        for child in self.children:
            child.validate(dataset)


class Root(Block, Element["Chunk"]):
    def __init__(self, document: 'Document', type: str, node: Chunk, comment: str) -> None:
        super().__init__(document, type)
        self.type = type
        self.node = node
        self.comment = comment

    def validate(self, dataset: Dataset) -> bool:
        # validate key-values
        for value in self.values:
            value.validate(dataset)

        # validate children
        self.validate_children(dataset)
        return True
    
    def validate_children(self, dataset: Dataset):
        # validate all children blocks
        for child in self.children:
            child.validate(dataset)
