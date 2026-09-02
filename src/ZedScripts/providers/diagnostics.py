from __future__ import annotations

import logging
import typing
from functools import singledispatchmethod

from lsprotocol.types import DiagnosticSeverity

import enum
from typing import ClassVar
from dataclasses import dataclass

from lsprotocol import types

from ..structure.parser import SyntaxErrorType
from ..structure.lexer import Token, TokenCollection, TextRange
from ..schema import SchemaType, SchemaBlock
from ..schema.types import SchemaTypeInteger, SchemaTypeFloat, SchemaTypeEnum, SchemaTypeString, SchemaTypeConst
from ..schema.validator import ResultVisitor, SchemaError
from ..workspace.document import Document


class DiagnosticType(enum.Enum):
    @classmethod
    def _missing_(cls, value: typing.Any) -> DiagnosticType | None:
        if isinstance(value, SyntaxErrorType):
            return cls["PARSER_" + value.name]
        return None

    PARSER_TOO_MANY_CLOSING_BRACKETS = enum.auto()
    PARSER_BLOCK_MISSING_TYPE = enum.auto()
    PARSER_BLOCK_NOT_CLOSED = enum.auto()

    SCHEMA_UNKNOWN_PARAMETER = enum.auto()
    SCHEMA_MISSING_REQUIRED_PARAMETER = enum.auto()
    SCHEMA_UNEXPECTED_BLOCK = enum.auto()
    SCHEMA_INVALID_BLOCK_ID = enum.auto()
    SCHEMA_VALUE_WRONG_TYPE = enum.auto()
    SCHEMA_VALUE_OUT_OF_RANGE = enum.auto()
    SCHEMA_VALUE_PATTERN_MATCH_FAILURE = enum.auto()
    SCHEMA_VALUE_INVALID_ENUM = enum.auto()
    SCHEMA_VALUE_INCORRECT_VALUE = enum.auto()
    SCHEMA_VALUE_SEQUENCE_MISSING_REQUIRED_ELEMENT = enum.auto()
    SCHEMA_VALUE_SEQUENCE_EXTRA_ELEMENTS = enum.auto()
    SCHEMA_UNEXPECTED_VALUE = enum.auto()


class DiagnosticDefinition:
    by_type: ClassVar[dict[DiagnosticType, DiagnosticDefinition]] = {}

    def __init__(self, type: DiagnosticType, severity: types.DiagnosticSeverity, args: dict[str, typing.Any]) -> None:
        self.type: DiagnosticType = type
        self.severity: types.DiagnosticSeverity = severity
        self.args: dict[str, typing.Any] = args

        DiagnosticDefinition.by_type[type] = self


@dataclass
class Diagnostic:
    type: DiagnosticType
    location: TextRange
    args: dict[str, typing.Any]


DiagnosticDefinition(DiagnosticType.PARSER_TOO_MANY_CLOSING_BRACKETS,
                     DiagnosticSeverity.Error,
                     {})

DiagnosticDefinition(DiagnosticType.PARSER_BLOCK_MISSING_TYPE,
                     DiagnosticSeverity.Error,
                     {})

DiagnosticDefinition(DiagnosticType.PARSER_BLOCK_NOT_CLOSED,
                     DiagnosticSeverity.Error,
                     {})

DiagnosticDefinition(DiagnosticType.SCHEMA_UNKNOWN_PARAMETER,
                     DiagnosticSeverity.Warning,
                     {"key": str})

DiagnosticDefinition(DiagnosticType.SCHEMA_MISSING_REQUIRED_PARAMETER,
                     DiagnosticSeverity.Warning,
                     {"key": str})

DiagnosticDefinition(DiagnosticType.SCHEMA_UNEXPECTED_BLOCK,
                     DiagnosticSeverity.Warning,
                     {})

DiagnosticDefinition(DiagnosticType.SCHEMA_VALUE_WRONG_TYPE,
                     DiagnosticSeverity.Warning,
                     {"expected": str})

DiagnosticDefinition(DiagnosticType.SCHEMA_VALUE_OUT_OF_RANGE,
                     DiagnosticSeverity.Warning,
                     {"min": float | int | None, "max": float | int | None})

DiagnosticDefinition(DiagnosticType.SCHEMA_VALUE_PATTERN_MATCH_FAILURE,
                     DiagnosticSeverity.Warning,
                     {"pattern": str})

DiagnosticDefinition(DiagnosticType.SCHEMA_VALUE_INVALID_ENUM,
                     DiagnosticSeverity.Warning,
                     {"members": list})

DiagnosticDefinition(DiagnosticType.SCHEMA_VALUE_INCORRECT_VALUE,
                     DiagnosticSeverity.Warning,
                     {"expected": str})

DiagnosticDefinition(DiagnosticType.SCHEMA_VALUE_SEQUENCE_MISSING_REQUIRED_ELEMENT,
                     DiagnosticSeverity.Warning,
                     {"name": str})

DiagnosticDefinition(DiagnosticType.SCHEMA_VALUE_SEQUENCE_EXTRA_ELEMENTS,
                     DiagnosticSeverity.Warning,
                     {})

DiagnosticDefinition(DiagnosticType.SCHEMA_UNEXPECTED_VALUE,
                     DiagnosticSeverity.Information,
                     {})

DiagnosticDefinition(DiagnosticType.SCHEMA_INVALID_BLOCK_ID,
                     DiagnosticSeverity.Information,
                     {"options": list})

# ensure that all diagnostic types have a corresponding definition
for diagnostic_type in DiagnosticType:
    assert diagnostic_type in DiagnosticDefinition.by_type


class DiagnosticsVisitor(ResultVisitor):
    def __init__(self, document: Document, delegate: ResultVisitor | None = None) -> None:
        super().__init__(delegate)
        self.document: Document = document

    def add_diagnostic(self, type: DiagnosticType, location: TextRange, args: dict[str, typing.Any]) -> None:
        self.document.diagnostics.append(
            Diagnostic(
                type=type,
                location=location,
                args=args
            )
        )

    def visit_block(self, schema: SchemaBlock,
                    block_type: TokenCollection | None, block_id: TokenCollection | None,
                    open_bracket: Token | None, close_bracket: Token | None,
                    errors: list[SchemaError]) -> None:
        # TODO: pass the bracket tokens so we can mark the entire block as an error
        for error in errors:
            if error is SchemaError.UNEXPECTED_BLOCK:
                self.add_diagnostic(
                    DiagnosticType.SCHEMA_UNEXPECTED_BLOCK,
                    TextRange(open_bracket.pos, close_bracket.end),
                    {}
                )
            elif error is SchemaError.MISSING_REQUIRED_PARAMETER:
                self.add_diagnostic(
                    DiagnosticType.SCHEMA_MISSING_REQUIRED_PARAMETER,
                    TextRange(close_bracket.pos, close_bracket.end),
                    {
                        "key": "TODO"
                    }
                )
            elif error is SchemaError.BLOCK_INVALID_ID:
                assert block_id is not None
                self.add_diagnostic(
                    DiagnosticType.SCHEMA_INVALID_BLOCK_ID,
                    TextRange(block_id[0].pos, block_id[-1].end),
                    {
                        "options": schema.valid_ids
                    }
                )
            else:
                logging.warning("Unexpected block error in DiagnosticsVisitor.visit_block: %s", error.name)

        super().visit_block(schema, block_type, block_id, open_bracket, close_bracket, errors)

    def visit_pair(self, schema: SchemaType | None, key: TokenCollection, equals: Token, value: TokenCollection,
                   errors: list[SchemaError]) -> None:
        for error in errors:
            if error is SchemaError.UNKNOWN_PARAMETER:
                self.add_diagnostic(
                    DiagnosticType.SCHEMA_UNKNOWN_PARAMETER,
                    TextRange(key[0].pos, value[-1].end),
                    {
                        "key": str(key)
                    }
                )
            elif error is SchemaError.VALUE_WRONG_TYPE:
                self.add_diagnostic(
                    DiagnosticType.SCHEMA_VALUE_WRONG_TYPE,
                    TextRange(value[0].pos, value[-1].end),
                    {
                        "expected": schema.basic
                    }
                )
            else:
                logging.warning("Unexpected schema error type in DiagnosticVisitor: %s", error.name)

        super().visit_pair(schema, key, equals, value, errors)

    def visit_value(self, schema: SchemaType | None, value: TokenCollection, errors: list[SchemaError]) -> None:
        location = TextRange(value[0].pos, value[-1].end)
        for error in errors:
            if error is SchemaError.UNEXPECTED_VALUE:
                self.add_diagnostic(
                    DiagnosticType.SCHEMA_UNEXPECTED_VALUE,
                    location,
                    {}
                )

        super().visit_value(schema, value, errors)

    @singledispatchmethod
    def visit_type(self, schema: SchemaType | None, tokens: TokenCollection,
                   start: int, length: int, errors: list[SchemaError]) -> None:
        super().visit_type(schema, tokens, start, length, errors)

    @visit_type.register
    def _(self, schema: SchemaTypeFloat, tokens: TokenCollection,
          start: int, length: int, errors: list[SchemaError]) -> None:
        range = TextRange(tokens.pos_of(start), tokens.pos_of(start + length))
        for error in errors:
            if error is SchemaError.VALUE_OUT_OF_RANGE:
                self.add_diagnostic(
                    DiagnosticType.SCHEMA_VALUE_OUT_OF_RANGE,
                    range,
                    {
                        "min": schema.min,
                        "max": schema.max
                    }
                )
            else:
                logging.warning("Unexpected schema error type in DiagnosticVisitor (float): %s", error.name)
        super().visit_type(schema, tokens, start, length, errors)

    @visit_type.register
    def _(self, schema: SchemaTypeInteger, tokens: TokenCollection,
          start: int, length: int, errors: list[SchemaError]) -> None:
        range = TextRange(tokens.pos_of(start), tokens.pos_of(start + length))
        for error in errors:
            if error is SchemaError.VALUE_OUT_OF_RANGE:
                self.add_diagnostic(
                    DiagnosticType.SCHEMA_VALUE_OUT_OF_RANGE,
                    range,
                    {
                        "min": schema.min,
                        "max": schema.max
                    }
                )
            else:
                logging.warning("Unexpected schema error type in DiagnosticVisitor (integer): %s", error.name)
        super().visit_type(schema, tokens, start, length, errors)

    @visit_type.register
    def _(self, schema: SchemaTypeEnum, tokens: TokenCollection,
          start: int, length: int, errors: list[SchemaError]) -> None:
        range = TextRange(tokens.pos_of(start), tokens.pos_of(start + length))
        for error in errors:
            if error is SchemaError.VALUE_INVALID_ENUM:
                self.add_diagnostic(
                    DiagnosticType.SCHEMA_VALUE_INVALID_ENUM,
                    range,
                    {
                        "members": list(schema.members.keys())
                    }
                )
            else:
                logging.warning("Unexpected schema error type in DiagnosticVisitor (enum): %s", error.name)
        super().visit_type(schema, tokens, start, length, errors)

    @visit_type.register
    def _(self, schema: SchemaTypeString, tokens: TokenCollection,
          start: int, length: int, errors: list[SchemaError]) -> None:
        range = TextRange(tokens.pos_of(start), tokens.pos_of(start + length))
        for error in errors:
            if error is SchemaError.VALUE_PATTERN_MATCH_FAILURE:
                self.add_diagnostic(
                    DiagnosticType.SCHEMA_VALUE_PATTERN_MATCH_FAILURE,
                    range,
                    {
                        "pattern": schema.pattern
                    }
                )
            else:
                logging.warning("Unexpected schema error type in DiagnosticVisitor (string): %s", error.name)
        super().visit_type(schema, tokens, start, length, errors)

    @visit_type.register
    def _(self, schema: SchemaTypeConst, tokens: TokenCollection,
          start: int, length: int, errors: list[SchemaError]) -> None:
        range = TextRange(tokens.pos_of(start), tokens.pos_of(start + length))
        for error in errors:
            if error is SchemaError.VALUE_INCORRECT_VALUE:
                self.add_diagnostic(
                    DiagnosticType.SCHEMA_VALUE_INCORRECT_VALUE,
                    range,
                    {
                        "expected": schema.value
                    }
                )
            else:
                logging.warning("Unexpected schema error type in DiagnosticVisitor (const): %s", error.name)
        super().visit_type(schema, tokens, start, length, errors)
