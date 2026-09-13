from __future__ import annotations

from lsprotocol.types import DiagnosticSeverity, DiagnosticTag

import enum
from typing import TYPE_CHECKING, ClassVar, Any
from dataclasses import dataclass

from lsprotocol import types

import ZedScripts
from ..utils import range_to_lsp
from ..enums.SyntaxErrorType import SyntaxErrorType
from ..structure.lexer import TextRange
from ..providers.locale import zedlocalizer

if TYPE_CHECKING:
    from ..enums.Diagnostic import DiagnosticType

type DiagnosticReport = (
      types.UnchangedDocumentDiagnosticReport
    | types.FullDocumentDiagnosticReport
)
"""Defines diagnostic report types to send to the client"""

type WorkspaceDiagnosticReport = (
      types.WorkspaceUnchangedDocumentDiagnosticReport
    | types.WorkspaceFullDocumentDiagnosticReport
)
"""Defines workspace diagnostic report types to send to the client"""


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

    def get_name(self) -> str:
        """Provides an identifier for the diagnostic type."""
        return self.type.name


@dataclass
class DiagnosticInfo:
    type: DiagnosticType
    location: TextRange
    args: dict[str, Any]


class DiagnosticCollection(list[DiagnosticInfo]):
    def to_lsp(self) -> list[types.Diagnostic]:
        """
        Converts the different diagnostic information into LSP-compatible diagnostics.
        """
        lsp_diagnostics: list[types.Diagnostic] = []
        for diagnostic in self:
            definition = DiagnosticDefinition.by_type[diagnostic.type]

            # ensure that the correct arguments are always passed
            for name, arg_type in definition.args.items():
                assert name in diagnostic.args, f"Missing argument '{name}' for diagnostic '{definition.get_name()}'"
                assert isinstance(diagnostic.args[name], arg_type), f"Argument '{name}' for diagnostic '{definition.get_name()}' must be of type '{arg_type.__name__}'"

            lsp_diagnostics.append(
                types.Diagnostic(
                    range=range_to_lsp(diagnostic.location),
                    message=zedlocalizer.localize_string(definition.type, definition,
                                                                args=diagnostic.args),
                    severity=definition.severity,
                    source=ZedScripts.SOURCE,
                    code=definition.get_name(),
                    tags=definition.tags
                )
            )
        return lsp_diagnostics

    def add(self, type: DiagnosticType, location: TextRange, args: dict[str, Any] = {}) -> None:
        self.append(DiagnosticInfo(type=type, location=location, args=args))

