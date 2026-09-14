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
    PARSER_TOO_MANY_CLOSING_BRACKETS =     enum.auto()
    PARSER_BLOCK_MISSING_TYPE =            enum.auto()
    PARSER_BLOCK_NOT_CLOSED =              enum.auto()

    # block diagnostics
    BLOCK_UNKNOWN_BLOCK =                  enum.auto()

    # ID related diagnostics
    BLOCK_UNEXPECTED_ID =                  enum.auto()
    BLOCK_MISSING_ID =                     enum.auto()
    BLOCK_HAS_ID_IN_PARENT =               enum.auto()
    BLOCK_ID_CANNOT_CONTAIN_SPACES =       enum.auto()
    BLOCK_INVALID_ID =                     enum.auto()
    BLOCK_FORBIDDEN_ID =                   enum.auto()

    # parameters diagnostics
    VALUE_UNKNOWN_PARAMETER =              enum.auto()
    VALUE_DEPRECATED_REPLACEMENT_VERSION = enum.auto()
    VALUE_DEPRECATED_REPLACEMENT =         enum.auto()
    VALUE_DEPRECATED_VERSION =             enum.auto()
    VALUE_DEPRECATED =                     enum.auto()
    VALUE_DUPLICATE =                      enum.auto()
    VALUE_MISSING =                        enum.auto()
    VALUE_FORBIDDEN =                      enum.auto()
    VALUE_INVALID_TYPE =                   enum.auto()
    VALUE_INVALID_OBJECT_FORMAT =            enum.auto()


# syntax diagnostics
DiagnosticDefinition(DiagnosticType.PARSER_TOO_MANY_CLOSING_BRACKETS,
                     DiagnosticSeverity.Error)
DiagnosticDefinition(DiagnosticType.PARSER_BLOCK_MISSING_TYPE,
                     DiagnosticSeverity.Error)
DiagnosticDefinition(DiagnosticType.PARSER_BLOCK_NOT_CLOSED,
                     DiagnosticSeverity.Error)

# block diagnostics
DiagnosticDefinition(DiagnosticType.BLOCK_UNKNOWN_BLOCK,
                     DiagnosticSeverity.Error,
                     args={"type": str},
                     tags=[DiagnosticTag.Unnecessary])

# ID related diagnostics
DiagnosticDefinition(DiagnosticType.BLOCK_UNEXPECTED_ID,
                     DiagnosticSeverity.Error,
                     args={"type": str, "id": str},
                     tags=[DiagnosticTag.Unnecessary])
DiagnosticDefinition(DiagnosticType.BLOCK_MISSING_ID,
                     DiagnosticSeverity.Error,
                     args={"type": str, "id": str})
DiagnosticDefinition(DiagnosticType.BLOCK_HAS_ID_IN_PARENT,
                     DiagnosticSeverity.Error,
                     args={"type": str, "parent_type": str, "invalid_blocks": list},
                     tags=[DiagnosticTag.Unnecessary])
DiagnosticDefinition(DiagnosticType.BLOCK_ID_CANNOT_CONTAIN_SPACES,
                     DiagnosticSeverity.Error,
                     args={"type": str, "id": str})
DiagnosticDefinition(DiagnosticType.BLOCK_INVALID_ID,
                     DiagnosticSeverity.Error,
                     args={"type": str, "id": str, "validIDs": list})
DiagnosticDefinition(DiagnosticType.BLOCK_FORBIDDEN_ID,
                     DiagnosticSeverity.Error,
                     args={"type": str, "id": str, "forbiddenIDs": list})

# parameter diagnostics
DiagnosticDefinition(DiagnosticType.VALUE_UNKNOWN_PARAMETER,
                     DiagnosticSeverity.Hint,
                     args={"type": str, "key": str},
                     tags=[DiagnosticTag.Unnecessary])
DiagnosticDefinition(DiagnosticType.VALUE_DEPRECATED_REPLACEMENT_VERSION,
                     DiagnosticSeverity.Warning,
                     args={"description": str, "replacement": str, "version": str},
                     tags=[DiagnosticTag.Deprecated])
DiagnosticDefinition(DiagnosticType.VALUE_DEPRECATED_REPLACEMENT,
                     DiagnosticSeverity.Warning,
                     args={"description": str, "replacement": str},
                     tags=[DiagnosticTag.Deprecated])
DiagnosticDefinition(DiagnosticType.VALUE_DEPRECATED_VERSION,
                     DiagnosticSeverity.Warning,
                     args={"description": str, "version": str},
                     tags=[DiagnosticTag.Deprecated])
DiagnosticDefinition(DiagnosticType.VALUE_DEPRECATED,
                     DiagnosticSeverity.Warning,
                     args={"description": str},
                     tags=[DiagnosticTag.Deprecated])
DiagnosticDefinition(DiagnosticType.VALUE_DUPLICATE,
                     DiagnosticSeverity.Warning,
                     args={"type": str, "key": str})
DiagnosticDefinition(DiagnosticType.VALUE_MISSING,
                     DiagnosticSeverity.Warning,
                     args={"type": str, "key": str})
DiagnosticDefinition(DiagnosticType.VALUE_FORBIDDEN,
                     DiagnosticSeverity.Warning,
                     args={"type": str, "key": str, "forbidden_values": list, "accepted_values": list})
DiagnosticDefinition(DiagnosticType.VALUE_INVALID_TYPE,
                     DiagnosticSeverity.Warning,
                     args={"type": str, "key": str, "expected_type": str, "actual_type": str})
DiagnosticDefinition(DiagnosticType.VALUE_INVALID_OBJECT_FORMAT,
                     DiagnosticSeverity.Warning,
                     args={"type": str, "key": str, "key_value_separator": str})



# ensure that all diagnostic types have a corresponding definition
for diagnostic_type in DiagnosticType:
    assert diagnostic_type in DiagnosticDefinition.by_type, f"Missing definition for diagnostic type: {diagnostic_type}"




