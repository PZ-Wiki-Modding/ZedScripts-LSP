import logging
import enum
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

from ..scripts.version import DataVersion


class DatasetTag(enum.Enum):
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