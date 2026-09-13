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

    # syntax diagnostics
    PARSER_TOO_MANY_CLOSING_BRACKETS = enum.auto()
    PARSER_BLOCK_MISSING_TYPE =        enum.auto()
    PARSER_BLOCK_NOT_CLOSED =          enum.auto()

    # block diagnostics
    SCHEMA_UNKNOWN_BLOCK =             enum.auto()

    # ID related diagnostics
    SCHEMA_UNEXPECTED_ID =             enum.auto()
    SCHEMA_MISSING_ID =                enum.auto()
    SCHEMA_HAS_ID_IN_PARENT =          enum.auto()
    SCHEMA_ID_CANNOT_CONTAIN_SPACES =  enum.auto()
    SCHEMA_INVALID_ID =                enum.auto()
    SCHEMA_FORBIDDEN_ID =              enum.auto()

    # parameters diagnostics
    SCHEMA_UNKNOWN_PARAMETER =         enum.auto()


# syntax diagnostics
DiagnosticDefinition(DiagnosticType.PARSER_TOO_MANY_CLOSING_BRACKETS,
                     DiagnosticSeverity.Error)
DiagnosticDefinition(DiagnosticType.PARSER_BLOCK_MISSING_TYPE,
                     DiagnosticSeverity.Error)
DiagnosticDefinition(DiagnosticType.PARSER_BLOCK_NOT_CLOSED,
                     DiagnosticSeverity.Error)

# block diagnostics
DiagnosticDefinition(DiagnosticType.SCHEMA_UNKNOWN_BLOCK,
                     DiagnosticSeverity.Error,
                     args={"type": str},
                     tags=[DiagnosticTag.Unnecessary])

# ID related diagnostics
DiagnosticDefinition(DiagnosticType.SCHEMA_UNEXPECTED_ID,
                     DiagnosticSeverity.Error,
                     args={"type": str, "id": str},
                     tags=[DiagnosticTag.Unnecessary])
DiagnosticDefinition(DiagnosticType.SCHEMA_MISSING_ID,
                     DiagnosticSeverity.Error,
                     args={"type": str, "id": str})
DiagnosticDefinition(DiagnosticType.SCHEMA_HAS_ID_IN_PARENT,
                     DiagnosticSeverity.Error,
                     args={"type": str, "parentType": str, "invalidBlocks": list},
                     tags=[DiagnosticTag.Unnecessary])
DiagnosticDefinition(DiagnosticType.SCHEMA_ID_CANNOT_CONTAIN_SPACES,
                     DiagnosticSeverity.Error,
                     args={"type": str, "id": str})
DiagnosticDefinition(DiagnosticType.SCHEMA_INVALID_ID,
                     DiagnosticSeverity.Error,
                     args={"type": str, "id": str, "validIDs": list})
DiagnosticDefinition(DiagnosticType.SCHEMA_FORBIDDEN_ID,
                     DiagnosticSeverity.Error,
                     args={"type": str, "id": str, "forbiddenIDs": list})

# parameter diagnostics
DiagnosticDefinition(DiagnosticType.SCHEMA_UNKNOWN_PARAMETER,
                     DiagnosticSeverity.Warning,
                     args={"key": str})



# ensure that all diagnostic types have a corresponding definition
for diagnostic_type in DiagnosticType:
    assert diagnostic_type in DiagnosticDefinition.by_type, f"Missing definition for diagnostic type: {diagnostic_type}"




