import logging
import enum
from pathlib import Path
from typing import Annotated, Optional
from pydantic import BaseModel, BeforeValidator, Field, WithJsonSchema

from lsprotocol.types import DiagnosticSeverity, DiagnosticTag

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



# define the models

class DatasetTag(enum.StrEnum):
    LATEST = "latest"
    STABLE = "stable"



class ReleaseModel(BaseModel):
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

class DatasetModel(BaseModel):
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

class DiagnosticsModel(BaseModel):
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

class ConfigurationModel(BaseModel):
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

    def find_diagnostic(self, type: DiagnosticType) -> DiagnosticsModel | None:
        for diagnostic in self.diagnostics:
            if diagnostic.type == type:
                return diagnostic
        return None

if __name__ == "__main__":
    import json
    config = ConfigurationModel()
    print(json.dumps(config.model_json_schema(), indent=4))