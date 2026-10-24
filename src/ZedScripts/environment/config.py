"""
Provides the configuration models and schema generation for the ZedScripts environment.

Usage:
    python -m ZedScripts.environment.config schema -o schema/zedscripts.json
    python -m ZedScripts.environment.config default -o default_config.json
"""
import logging
import enum
from pathlib import Path
from typing import Annotated, Optional
from pydantic import BaseModel, BeforeValidator, Field, WithJsonSchema, ConfigDict

from lsprotocol.types import DiagnosticSeverity, DiagnosticTag

from ..environment import LoggerLevel
from ..scripts.version import DataVersion
from ..enums.Diagnostic import DiagnosticType



# the auto enum of DiagnosticType makes them lowercase, but we'll want to use
# uppercase, that is the member's name

def _parse_diagnostic_type_name(value: object) -> object:
    if isinstance(value, DiagnosticType):
        return value
    if isinstance(value, str):
        try:
            return DiagnosticType[value]
        except KeyError:
            raise ValueError("type must be a DiagnosticType member name") from None
    return value
DiagnosticTypeName = Annotated[
    DiagnosticType,
    BeforeValidator(_parse_diagnostic_type_name),
    WithJsonSchema({
        "type": "string",
        "enum": [member.name for member in DiagnosticType],
    }),
]

def _parse_diagnostic_severity_name(value: object) -> object:
    if isinstance(value, DiagnosticSeverity):
        return value
    if isinstance(value, str):
        try:
            return DiagnosticSeverity[value]
        except KeyError:
            raise ValueError("severity must be a DiagnosticSeverity member name") from None
    return value
DiagnosticSeverityName = Annotated[
    DiagnosticSeverity,
    BeforeValidator(_parse_diagnostic_severity_name),
    WithJsonSchema({
        "type": "string",
        "enum": [member.name for member in DiagnosticSeverity],
    }),
]

def _parse_diagnostic_tag_name(value: object) -> object:
    if isinstance(value, DiagnosticTag):
        return value
    if isinstance(value, str):
        try:
            return DiagnosticTag[value]
        except KeyError:
            raise ValueError("tag must be a DiagnosticTag member name") from None
    return value
DiagnosticTagName = Annotated[
    DiagnosticTag,
    BeforeValidator(_parse_diagnostic_tag_name),
    WithJsonSchema({
        "type": "string",
        "enum": [member.name for member in DiagnosticTag],
    }),
]

def _parse_logger_level_name(value: object) -> object:
    if isinstance(value, LoggerLevel):
        return value
    if isinstance(value, str):
        try:
            return LoggerLevel[value]
        except KeyError:
            raise ValueError("level must be a LoggerLevel member name") from None
    return value
LoggerLevelName = Annotated[
    LoggerLevel,
    BeforeValidator(_parse_logger_level_name),
    WithJsonSchema({
        "type": "string",
        "enum": [member.name for member in LoggerLevel],
    }),
]



# define the models

class DatasetTag(enum.StrEnum):
    LATEST = "latest"
    STABLE = "stable"


class ZedBaseModel(BaseModel):
    """Base model for all ZedScripts configuration models.
    Notably used to set additionalProperties to false for everything."""
    model_config = ConfigDict(extra='forbid')


class ReleaseModel(ZedBaseModel):
    major: int = Field(
        description="Build game version number.",
        ge=42,
    )
    minor: int = Field(
        description="Minor game version number.",
        ge=0,
    )
    patch: int = Field(
        description="Patch game version number.",
        ge=0,
    )
    version: Optional[int] = Field(
        description="Dataset version number for the provided Build release (major.minor.patch). This is incremented whenever the dataset for a specific version is updated.",
        default=None,
        ge=0,
    )

class LocalDatasetModel(ZedBaseModel):
    blocks: Optional[str] = Field(
        description="Local path to the blocks dataset file.",
        default=None,
    )
    roots: Optional[str] = Field(
        description="Local path to the roots dataset file.",
        default=None,
    )

class DatasetModel(ZedBaseModel):
    release: Optional[ReleaseModel] = Field(
        description="Provides a configuration for the dataset version to use for validation. This overrides the `latest` and `stable` fields if set.",
        default=None,
    )
    latest: Optional[bool] = Field(
        description="Indicates whether to use the latest dataset version for validation. This is ignored if `release` is set. Overrides the `stable` field if set.",
        default=False,
    )
    stable: Optional[bool] = Field(
        description="Provides a configuration for the stable dataset version to use for validation. Ignored if `release` or `latest` is set.",
        default=True,
    )
    local: Optional[LocalDatasetModel] = Field(
        description="Provides local dataset file paths for blocks and roots.",
        default=None,
    )

    def to_data_version(self) -> DataVersion | DatasetTag:
        if self.release is None:
            if self.latest:
                return DatasetTag.LATEST
            if self.stable:
                return DatasetTag.STABLE
            logging.warning("No dataset version specified, defaulting to 'stable'.")
            return DatasetTag.STABLE
        from ..scripts.dataset import Manifest
        try:
            return Manifest.from_release_model(self.release)
        except Exception as e:
            logging.error(f"Failed to get data version from release model: {e}. Defaulting to 'stable'.")
            return DatasetTag.STABLE

class DiagnosticsModel(ZedBaseModel):
    """Represents the diagnostics configuration for the workspace environment."""
    type: DiagnosticTypeName = Field(
        description="Specifies the diagnostic member name to enable.",
    )
    enable: Optional[bool] = Field(
        description="Indicates whether diagnostics are enabled.",
        default=True,
    )
    severity: Optional[DiagnosticSeverityName] = Field(
        description="Specifies the severity level of the diagnostics.",
        default=None,
    )
    tags: Optional[list[DiagnosticTagName]] = Field(
        description="Specifies the tags associated with the diagnostics.",
        default=None,
    )

class ServerModel(ZedBaseModel):
    """Represents the server configuration for the workspace environment."""
    logging_level: Optional[LoggerLevelName] = Field(
        description="Specifies the logging level for the server. This option only works in the global configuration.",
        default=LoggerLevel.INFO,
        exclude=True,
    )

class ConfigurationModel(ZedBaseModel):
    """Represents the content of the configuration files for workspace environments."""
    dataset: DatasetModel = Field(
        description="Provides configuration for the dataset version to use for diagnostics.",
        default_factory=DatasetModel,
    )
    libraries: set[Path] = Field(
        description="Set of library folders to reference. Usually this should contain the base game folder.",
        default_factory=set,
    )
    ignored: set[str] = Field(
        description="Regex patterns for files and folders to ignore in the workspace.",
        default=set([
            r"tileGeometry\.txt",
            r"tileDepthTextureAssignments\.txt",
            r".+\.tiles\.txt"
        ]),
    )
    diagnostics: list[DiagnosticsModel] = Field(
        description="List of diagnostics configurations for the workspace environment.",
        default_factory=list,
    )
    server: ServerModel = Field(
        description="Provides configuration for the server in the workspace environment.",
        default_factory=ServerModel,
    )

    def find_diagnostic(self, type: DiagnosticType) -> DiagnosticsModel | None:
        for diagnostic in self.diagnostics:
            if diagnostic.type == type:
                return diagnostic
        return None

if __name__ == "__main__":
    import argparse

    def print_schema(args: argparse.Namespace):
        import json
        config = ConfigurationModel()
        out = json.dumps(config.model_json_schema(), indent=4)
        print(out)
        if args.output_path:
            with open(args.output_path, "w") as f:
                f.write(out)

    def print_default_config(args: argparse.Namespace):
        config = ConfigurationModel()
        out = config.model_dump_json(indent=4)
        print(out)
        if args.output_path:
            with open(args.output_path, "w") as f:
                f.write(out)

    main_parser = argparse.ArgumentParser(description="ZedScripts configuration tool")

    # schema generation command
    subparser = main_parser.add_subparsers(
        dest="command",
        required=True,
        help="Available commands"
    )
    schema_parser = subparser.add_parser("schema", 
                                         help="Print the JSON schema of the configuration model.")
    schema_parser.add_argument("-o", "--output-path", 
                               help="Path to output the JSON schema.")
    schema_parser.set_defaults(func=print_schema)

    # default configuration command
    default_config_subparser = subparser.add_parser("default", 
                                                    help="Print the default configuration of the workspace environment.")
    default_config_subparser.add_argument("-o", "--output-path", 
                                          help="Path to output the default configuration.")
    default_config_subparser.set_defaults(func=print_default_config)

    args = main_parser.parse_args()

    args.func(args)