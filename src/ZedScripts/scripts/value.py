from typing import TYPE_CHECKING

from . import Element
from ..enums.Diagnostic import DiagnosticType
from ..structure.ast import ValueNode
from ..structure.lexer import TextRange
from ..providers.semantic_tokens import SemanticTokenType, SemanticTokenModifiers

if TYPE_CHECKING:
    from ..scripts.dataset import Dataset


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

    def validate(self, dataset: 'Dataset') -> bool:
        #TODO: to implement
        return True
