from __future__ import annotations

from lsprotocol.types import DiagnosticSeverity, DiagnosticTag

import enum
from typing import ClassVar, Any
from dataclasses import dataclass

from lsprotocol import types

from ..structure.parser import SyntaxErrorType
from ..structure.lexer import Token, TokenCollection, TextRange


class DiagnosticType(enum.Enum):
    @classmethod
    def _missing_(cls, value: Any) -> DiagnosticType | None:
        if isinstance(value, SyntaxErrorType):
            return cls["PARSER_" + value.name]
        return None

    PARSER_TOO_MANY_CLOSING_BRACKETS =                          enum.auto()
    PARSER_BLOCK_MISSING_TYPE =                                 enum.auto()
    PARSER_BLOCK_NOT_CLOSED =                                   enum.auto()

    SCHEMA_UNKNOWN_PARAMETER =                                  enum.auto()
    SCHEMA_MISSING_REQUIRED_PARAMETER =                         enum.auto()
    SCHEMA_UNEXPECTED_BLOCK =                                   enum.auto()
    SCHEMA_INVALID_BLOCK_ID =                                   enum.auto()
    SCHEMA_VALUE_WRONG_TYPE =                                   enum.auto()
    SCHEMA_VALUE_OUT_OF_RANGE =                                 enum.auto()
    SCHEMA_VALUE_PATTERN_MATCH_FAILURE =                        enum.auto()
    SCHEMA_VALUE_INVALID_ENUM =                                 enum.auto()
    SCHEMA_VALUE_INCORRECT_VALUE =                              enum.auto()
    SCHEMA_VALUE_SEQUENCE_MISSING_REQUIRED_ELEMENT =            enum.auto()
    SCHEMA_VALUE_SEQUENCE_EXTRA_ELEMENTS =                      enum.auto()
    SCHEMA_UNEXPECTED_VALUE =                                   enum.auto()


class DiagnosticDefinition:
    by_type: ClassVar[dict[DiagnosticType, DiagnosticDefinition]] = {}

    def __init__(self, 
                 type: DiagnosticType, 
                 severity: types.DiagnosticSeverity, 
                 args: dict[str, Any] = {},
                 tags: list[DiagnosticTag] = [],
                ) -> None:
        self.type: DiagnosticType = type
        self.severity: types.DiagnosticSeverity = severity
        self.args: dict[str, Any] = args
        self.tags: list[DiagnosticTag] = tags

        DiagnosticDefinition.by_type[type] = self


@dataclass
class Diagnostic:
    type: DiagnosticType
    location: TextRange
    args: dict[str, Any]


DiagnosticDefinition(DiagnosticType.PARSER_TOO_MANY_CLOSING_BRACKETS,
                     DiagnosticSeverity.Error)

DiagnosticDefinition(DiagnosticType.PARSER_BLOCK_MISSING_TYPE,
                     DiagnosticSeverity.Error)

DiagnosticDefinition(DiagnosticType.PARSER_BLOCK_NOT_CLOSED,
                     DiagnosticSeverity.Error)



DiagnosticDefinition(DiagnosticType.SCHEMA_UNKNOWN_PARAMETER,
                     DiagnosticSeverity.Warning,
                     args={"key": str})

DiagnosticDefinition(DiagnosticType.SCHEMA_MISSING_REQUIRED_PARAMETER,
                     DiagnosticSeverity.Warning,
                     args={"key": str})

DiagnosticDefinition(DiagnosticType.SCHEMA_UNEXPECTED_BLOCK,
                     DiagnosticSeverity.Warning)

DiagnosticDefinition(DiagnosticType.SCHEMA_VALUE_WRONG_TYPE,
                     DiagnosticSeverity.Warning,
                     args={"expected": str})

DiagnosticDefinition(DiagnosticType.SCHEMA_VALUE_OUT_OF_RANGE,
                     DiagnosticSeverity.Warning,
                     args={"min": float | int | None, "max": float | int | None})

DiagnosticDefinition(DiagnosticType.SCHEMA_VALUE_PATTERN_MATCH_FAILURE,
                     DiagnosticSeverity.Warning,
                     args={"pattern": str})

DiagnosticDefinition(DiagnosticType.SCHEMA_VALUE_INVALID_ENUM,
                     DiagnosticSeverity.Warning,
                     args={"members": list})

DiagnosticDefinition(DiagnosticType.SCHEMA_VALUE_INCORRECT_VALUE,
                     DiagnosticSeverity.Warning,
                     args={"expected": str})

DiagnosticDefinition(DiagnosticType.SCHEMA_VALUE_SEQUENCE_MISSING_REQUIRED_ELEMENT,
                     DiagnosticSeverity.Warning,
                     args={"name": str})

DiagnosticDefinition(DiagnosticType.SCHEMA_VALUE_SEQUENCE_EXTRA_ELEMENTS,
                     DiagnosticSeverity.Warning)

DiagnosticDefinition(DiagnosticType.SCHEMA_UNEXPECTED_VALUE,
                     DiagnosticSeverity.Information)

DiagnosticDefinition(DiagnosticType.SCHEMA_INVALID_BLOCK_ID,
                     DiagnosticSeverity.Information,
                     args={"options": list})

# ensure that all diagnostic types have a corresponding definition
for diagnostic_type in DiagnosticType:
    assert diagnostic_type in DiagnosticDefinition.by_type, f"Missing definition for diagnostic type: {diagnostic_type}"

