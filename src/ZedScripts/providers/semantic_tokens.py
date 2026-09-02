from __future__ import annotations

import enum
import re
from operator import attrgetter

from lsprotocol.types import SemanticTokens

from ..structure.lexer import TokenType, chars_in_range, Token, TokenCollection, TextPosition, TextRange

from typing import TYPE_CHECKING

from ..schema import SchemaType, SchemaBlock
from ..schema.validator import SchemaError, ResultVisitor

if TYPE_CHECKING:
    from ..workspace.document import Document

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


class SemanticTokenModifiers(enum.IntFlag):
    DECLARATION = enum.auto()
    DEFINITION = enum.auto()
    READONLY = enum.auto()
    STATIC = enum.auto()
    DEPRECATED = enum.auto()
    ABSTRACT = enum.auto()
    ASYNC = enum.auto()
    MODIFICATION = enum.auto()
    DOCUMENTATION = enum.auto()
    DEFAULT_LIBRARY = enum.auto()


class SemanticToken:
    def __init__(
            self, range: TextRange, type: SemanticTokenType, modifiers: SemanticTokenModifiers | None = None
    ) -> None:
        if modifiers is None:
            modifiers = SemanticTokenModifiers(0)
        self.range: TextRange = range
        self.type: SemanticTokenType = type
        self.modifiers: SemanticTokenModifiers = modifiers


class SemanticTokensVisitor(ResultVisitor):
    """
    Value visitor that adds semantic tokens for the values encountered.
    """
    def __init__(self, document: Document, delegate: ResultVisitor | None = None) -> None:
        super().__init__(delegate)
        self.document: Document = document

    def add_semantic_token(
            self, location: TextRange,
            type: SemanticTokenType, modifiers: SemanticTokenModifiers | None = None) -> None:
        self.document.semantic_tokens.append(
            SemanticToken(
                location,
                type,
                modifiers
            )
        )

    def visit_type(self, schema: SchemaType | None, tokens: TokenCollection,
                   start: int, length: int, errors: list[SchemaError]) -> None:
        range = TextRange(tokens.pos_of(start), tokens.pos_of(start + length))
        if schema is None:
            # add token for non-schema parameters
            token_type = SemanticTokenType.STRING
            if re.fullmatch(PATTERN_FLOAT, str(tokens)[start:start + length]) is not None:
                token_type = SemanticTokenType.NUMBER
            self.add_semantic_token(
                range,
                token_type
            )
            return

        match schema.basic:
            case "sequence":
                # might want to add tokens for separators
                return
            case "list":
                # might want to add tokens for delimiters
                return
            case "const":
                return

        token_type: SemanticTokenType
        match schema.basic:
            case "string":
                token_type = SemanticTokenType.STRING
            case "reference":
                token_type = SemanticTokenType.VARIABLE
            case "enum":
                token_type = SemanticTokenType.ENUM_MEMBER
            case "integer":
                token_type = SemanticTokenType.NUMBER
            case "float":
                token_type = SemanticTokenType.NUMBER
            case "boolean":
                token_type = SemanticTokenType.KEYWORD
            case _:
                raise RuntimeError("Unrecognised SchemaType in SemanticTokenVisitor.visit")

        self.add_semantic_token(range, token_type)
        super().visit_type(schema, tokens, start, length, errors)

    def visit_pair(self, schema: SchemaType | None, key: TokenCollection, equals: Token, value: TokenCollection,
                   errors: list[SchemaError]) -> None:
        self.add_semantic_token(
            TextRange(key[0].pos, key[-1].end),
            SemanticTokenType.PROPERTY
        )
        self.add_semantic_token(
            TextRange(equals.pos, equals.end),
            SemanticTokenType.OPERATOR
        )

        super().visit_pair(schema, key, equals, value, errors)

    def visit_block(self, schema: SchemaBlock,
                    block_type: TokenCollection | None, block_id: TokenCollection | None,
                    open_bracket: Token | None, close_bracket: Token | None,
                    errors: list[SchemaError]) -> None:
        if block_type is not None:
            self.add_semantic_token(
                TextRange(block_type[0].pos, block_type[-1].end),
                SemanticTokenType.TYPE
            )
        if block_id is not None:
            self.add_semantic_token(
                TextRange(block_id[0].pos, block_id[-1].end),
                SemanticTokenType.VARIABLE
            )
        super().visit_block(schema, block_type, block_id, open_bracket, close_bracket, errors)


def build_syntactic_tokens(document: Document) -> list[SemanticToken]:
    """
    Builds tokens that can be inferred directly from the lexical tokens without further context.
    :param document:
    :return:
    """
    semantic_tokens: list[SemanticToken] = []
    for token in document.lexical_tokens:
        match token.type:
            case TokenType.PUNCTUATOR:
                semantic_tokens.append(
                    SemanticToken(
                        TextRange(token.pos, token.end),
                        SemanticTokenType.KEYWORD
                    )
                )
            case TokenType.COMMENT:
                semantic_tokens.append(
                    SemanticToken(
                        TextRange(token.pos, token.end),
                        SemanticTokenType.COMMENT
                    )
                )

    return semantic_tokens


def tokens_to_lsp(document: Document) -> SemanticTokens:
    lsp_tokens: list[int] = []
    last_pos: TextPosition = TextPosition(0, 0)
    semantic_tokens = sorted(document.semantic_tokens, key=attrgetter("range.start.line", "range.start.offset"))
    for i in range(len(semantic_tokens)):
        token = semantic_tokens[i]

        line_delta = token.range.start.line - last_pos.line
        if line_delta == 0:
            offset_delta = token.range.start.offset - last_pos.offset
        else:
            offset_delta = token.range.start.offset

        characters = chars_in_range(document.text, token.range)
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

    return SemanticTokens(lsp_tokens)
