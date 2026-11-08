from __future__ import annotations

from lsprotocol import types

from typing import TYPE_CHECKING, ClassVar, Any
from dataclasses import dataclass


import ZedScripts
from ..utils import textrange_to_lsp
from ..structure.lexer import TextRange
from ..providers.locale import zedlocalizer

if TYPE_CHECKING:
    from ..server import ZedServer
    from ..environment.config import ConfigurationModel
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
                 tags: list[types.DiagnosticTag] = [],
                 needs_init: bool = False,
                 is_debug: bool = False,
                ) -> None:
        self.type: DiagnosticType = type
        self.severity: types.DiagnosticSeverity = severity
        self.args: dict[str, Any] = args
        self.tags: list[types.DiagnosticTag] = tags
        self.requires_initialization: bool = needs_init
        self.is_debug: bool = is_debug

        DiagnosticDefinition.by_type[type] = self

    @staticmethod
    def get(type: DiagnosticType) -> DiagnosticDefinition:
        assert type in DiagnosticDefinition.by_type, f"WEIRD: Diagnostic type '{type}' is not registered, but this is verified earlier"
        return DiagnosticDefinition.by_type[type]

    def get_name(self) -> str:
        """Provides an identifier for the diagnostic type."""
        return self.type.name

    def get_severity(self) -> types.DiagnosticSeverity:
        return self.severity

    def get_tags(self) -> list[types.DiagnosticTag]:
        return self.tags

    def needs_initialization(self) -> bool:
        return self.requires_initialization


@dataclass
class DiagnosticInfo:
    type: DiagnosticType
    location: TextRange
    args: dict[str, Any]


class DiagnosticCollection(list[DiagnosticInfo]):
    def to_lsp(self, server: 'ZedServer', config: ConfigurationModel, 
               remove_pre_init: bool = False,
               ignore_none: bool = False) -> list[types.Diagnostic]:
        """
        Converts the different diagnostic information into LSP-compatible diagnostics.

        Returns:
            list[types.Diagnostic]: A list of LSP-compatible diagnostic objects.
        """
        lsp_diagnostics: list[types.Diagnostic] = []
        for diagnostic in reversed(self):
            definition = DiagnosticDefinition.get(diagnostic.type)

            if definition.is_debug and not ZedScripts.IS_DEBUG:
                continue

            if not ignore_none:
                if definition.needs_initialization():
                    if not remove_pre_init and not server.is_initialized:
                        continue
                elif remove_pre_init:
                    continue

            severity = definition.get_severity()
            tags = definition.get_tags()

            config_def = config.find_diagnostic(diagnostic.type)
            if config_def is not None:
                config_severity = config_def.severity
                if config_severity is not None:
                    severity = config_severity
                config_tags = config_def.tags
                if config_tags is not None:
                    tags = config_tags

            # ensure that the correct arguments are always passed
            for name, arg_type in definition.args.items():
                assert name in diagnostic.args, f"Missing argument '{name}' for diagnostic '{definition.get_name()}'"
                assert isinstance(diagnostic.args[name], arg_type), f"Argument '{name}' for diagnostic '{definition.get_name()}' must be of type '{arg_type.__name__}'"

            lsp_diagnostics.append(
                types.Diagnostic(
                    range=textrange_to_lsp(diagnostic.location),
                    message=zedlocalizer.localize_string(definition.type, definition,
                                                                args=diagnostic.args),
                    severity=severity,
                    source=ZedScripts.DIAGNOSTICS_SOURCE,
                    code=definition.get_name(),
                    tags=tags
                )
            )
        return lsp_diagnostics

    def add(self, config: ConfigurationModel, type: DiagnosticType, location: TextRange, args: dict[str, Any] = {}) -> None:
        """
        Adds a new diagnostic to the collection.

        Args:
            config (ConfigurationModel): The configuration model to use for the diagnostic.
            type (DiagnosticType): The type of the diagnostic.
            location (TextRange): The location in the text where the diagnostic applies.
            args (dict[str, Any], optional): Additional arguments for the diagnostic. Defaults to {}.
        """
        config_def = config.find_diagnostic(type)
        if config_def is not None:
            enabled = config_def.enable
            if not enabled:
                return
        self.append(DiagnosticInfo(type=type, location=location, args=args))

