from __future__ import annotations

import enum
import re
import logging
from typing import TYPE_CHECKING, cast
from operator import attrgetter

from lsprotocol.types import SemanticTokens

from .. import IS_DEBUG
from ..structure.lexer import TokenType, chars_in_range, Token, TokenCollection, TextPosition, TextRange

if TYPE_CHECKING:
    from ..environment.document import Document

PATTERN_FLOAT = re.compile("-?\\d+(?:\\.\\d+)?")


class SemanticTokenType(enum.IntEnum):
    NAMESPACE = 0
    TYPE = 1
    CLASS = 2
    ENUM = 3
    INTERFACE = 4
    STRUCT = 5
    TYPE_PARAMETER = 6
    PARAMETER = 7
    VARIABLE = 8
    PROPERTY = 9
    ENUM_MEMBER = 10
    EVENT = 11
    FUNCTION = 12
    METHOD = 13
    MACRO = 14
    KEYWORD = 15
    MODIFIER = 16
    COMMENT = 17
    STRING = 18
    NUMBER = 19
    REGEXP = 20
    OPERATOR = 21
    DECORATOR = 22
    LABEL = 23


class SemanticTokenModifiers(enum.IntFlag):
    DECLARATION = enum.auto()
    """declaration site of a symbol"""
    DEFINITION = enum.auto()
    """definition (vs. just a declaration)"""
    READONLY = enum.auto()
    """symbol can't be reassigned (e.g. a constant)"""
    STATIC = enum.auto()
    """static member/variable"""
    DEPRECATED = enum.auto()
    """symbol is deprecated, editors often show strikethrough"""
    ABSTRACT = enum.auto()
    """abstract method/class"""
    ASYNC = enum.auto()
    """async function/method"""
    MODIFICATION = enum.auto()
    """token is a write/assignment to the symbol, not just a read"""
    DOCUMENTATION = enum.auto()
    """token appears inside documentation"""
    DEFAULT_LIBRARY = enum.auto()
    """symbol comes from a built-in/default library"""

def get_tokens() -> tuple[list[str], list[str]]:
    """
    Returns the list of semantic token types and modifiers as strings.
    """
    return [t.name.lower() for t in SemanticTokenType], [cast(str, m.name).lower() for m in SemanticTokenModifiers]






class SemanticToken:
    def __init__(
            self, range: TextRange, type: SemanticTokenType, modifiers: SemanticTokenModifiers | None = None
    ) -> None:
        if modifiers is None:
            modifiers = SemanticTokenModifiers(0)
        self.range: TextRange = range
        self.type: SemanticTokenType = type
        self.modifiers: SemanticTokenModifiers = modifiers

    def __repr__(self) -> str:
        return f"SemanticToken(range={self.range}, type={self.type.name}[{self.type}], modifiers={self.modifiers})"


class SemanticTokenCollection(list[SemanticToken]):
    def __init__(self, document: Document, *args: SemanticToken) -> None:
        super().__init__(args)
        self.document = document

    def sort_tokens(self) -> "SemanticTokenCollection":
        self.sort(key=attrgetter("range.start.line", "range.start.offset"))
        return self

    def to_lsp(self) -> list[int]:
        lsp_tokens: list[int] = []
        last_pos: TextPosition = TextPosition(0, 0)

        # make sure to sort the semantic tokens by their position
        semantic_tokens = self.sort_tokens()
        for i in range(len(semantic_tokens)):
            token = semantic_tokens[i]

            line_delta = token.range.start.line - last_pos.line
            if line_delta == 0:
                offset_delta = token.range.start.offset - last_pos.offset
            else:
                offset_delta = token.range.start.offset

            characters = chars_in_range(self.document.text, token.range)
            if characters == "":
                continue

            lines = characters.split("\n")
            lsp_tokens.append(line_delta)
            lsp_tokens.append(offset_delta)
            lsp_tokens.append(len(lines[0]))
            lsp_tokens.append(token.type.value)
            # false positive U_U
            lsp_tokens.append(int(token.modifiers))
            for line in lines[1:]:
                lsp_tokens.append(1)
                lsp_tokens.append(0)
                lsp_tokens.append(len(line))
                lsp_tokens.append(token.type.value)
                # false positive U_U
                lsp_tokens.append(int(token.modifiers))

            last_pos = token.range.start if len(lines) == 1 else TextPosition(token.range.start.line + len(lines) - 1, 0)

        # just so we don't have a for loop when not in debug mode
        # if IS_DEBUG:
        #     logging.debug("Semantic tokens for document")
        #     max_token_length = 70
        #     for line, token in enumerate(semantic_tokens):
        #         logging.debug(f"{str(token).ljust(max_token_length+2)} {lsp_tokens[line * 5: (line + 1) * 5]}")

        return lsp_tokens

    def add(self, type: SemanticTokenType, location: TextRange, modifiers: list[SemanticTokenModifiers] = []):
        """
        Add a new semantic token to the collection.

        Args:
            type (SemanticTokenType): The type of the semantic token.
            location (TextRange): The range in the document that the token covers.
        """
        combined_modifiers = SemanticTokenModifiers(0)
        for modifier in modifiers:
            combined_modifiers |= modifier
        self.append(SemanticToken(location, type, combined_modifiers))


def build_syntactic_tokens(document: Document):
    """
    Builds tokens that can be inferred directly from the lexical tokens without further context.
    :param document:
    :return:
    """
    semantic_tokens = document.syntactic_semantic_tokens
    semantic_tokens.clear() # reset syntactic semantic tokens

    # mark every typical lexical token with a corresponding semantic token
    for token in document.lexical_tokens:
        match token.type:
            case TokenType.ELEMENT_DELIMITER:
                semantic_tokens.add(
                    SemanticTokenType.KEYWORD,
                    TextRange(token.pos, token.end),
                )
            case TokenType.COMMENT:
                semantic_tokens.add(
                    SemanticTokenType.COMMENT,
                    TextRange(token.pos, token.end),
                )
            case TokenType.PUNCTUATOR:
                semantic_tokens.add(
                    SemanticTokenType.KEYWORD,
                    TextRange(token.pos, token.end),
                )

