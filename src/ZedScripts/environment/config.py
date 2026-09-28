import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


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
