import enum
from typing import Any

from lsprotocol.types import DiagnosticSeverity, DiagnosticTag

from ..enums.SyntaxErrorType import SyntaxErrorType
from ..providers.diagnostics import DiagnosticDefinition


class DiagnosticType(enum.Enum):
    @classmethod
    def _missing_(cls, value: Any) -> 'DiagnosticType | None':
        if isinstance(value, SyntaxErrorType):
            return cls["PARSER_" + value.name]
        return None

    PARSER_TOO_MANY_CLOSING_BRACKETS = enum.auto()
    PARSER_BLOCK_MISSING_TYPE =        enum.auto()
    PARSER_BLOCK_NOT_CLOSED =          enum.auto()

    SCHEMA_UNKNOWN_BLOCK =             enum.auto()
    SCHEMA_UNEXPECTED_ID =             enum.auto()

    SCHEMA_UNKNOWN_PARAMETER =         enum.auto()



DiagnosticDefinition(DiagnosticType.PARSER_TOO_MANY_CLOSING_BRACKETS,
                     DiagnosticSeverity.Error)
DiagnosticDefinition(DiagnosticType.PARSER_BLOCK_MISSING_TYPE,
                     DiagnosticSeverity.Error)
DiagnosticDefinition(DiagnosticType.PARSER_BLOCK_NOT_CLOSED,
                     DiagnosticSeverity.Error)

DiagnosticDefinition(DiagnosticType.SCHEMA_UNKNOWN_BLOCK,
                     DiagnosticSeverity.Error,
                     args={"type": str})
DiagnosticDefinition(DiagnosticType.SCHEMA_UNEXPECTED_ID,
                     DiagnosticSeverity.Error,
                     args={"id": str})

DiagnosticDefinition(DiagnosticType.SCHEMA_UNKNOWN_PARAMETER,
                     DiagnosticSeverity.Warning,
                     args={"key": str})



# ensure that all diagnostic types have a corresponding definition
for diagnostic_type in DiagnosticType:
    assert diagnostic_type in DiagnosticDefinition.by_type, f"Missing definition for diagnostic type: {diagnostic_type}"




