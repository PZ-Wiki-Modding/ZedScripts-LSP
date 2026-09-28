import enum
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class WorkspaceType(enum.Enum):
    """Represents different types of workspace folders."""
    LIBRARY = enum.auto()
    """A library defined by the user to reference things from.
    No validation should be performed on it."""
    PROJECT = enum.auto()
    """A workspace folder."""
    SOLITARY = enum.auto()
    """Files that are not opened as part of a workspace 
    or library but should still be validated.
    
    This workspace always exists and just holds solitary files."""

class VersionType(enum.StrEnum):
    """Represents different version types the workspace folders follow."""
    PRE_42 = enum.auto()
    """Modded pre-42 folder structure."""
    VERSIONING = enum.auto()
    """Modded versioning folder.
    
    https://pzwiki.net/wiki/Mod_structure#Common_and_versioning_folders"""
    COMMON = enum.auto()
    """Modded folder `common`.
    
    https://pzwiki.net/wiki/Mod_structure#Common_and_versioning_folders"""
    OTHER = enum.auto()
    """Other uncategorized version."""
    BASE_GAME = enum.auto()
    """Base game files (e.g., `ProjectZomboid/media`)."""




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
    version: int = Field(
        description="Dataset version number for the provided Build release (major.minor.patch). This is incremented whenever the dataset for a specific version is updated.",
        ge=1,
    )

class DatasetModel(BaseModel):
    release: Optional[ReleaseModel] = Field(
        description="Provides a configuration for the dataset version to use for validation. This overrides the `latest` field if set.",
        default=None,
    )
    latest: Optional[bool] = Field(
        description="Indicates whether to use the latest dataset version for validation.",
        default=True,
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
