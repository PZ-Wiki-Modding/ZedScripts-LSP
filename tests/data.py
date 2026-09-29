data_global = {
    "dataset": {
        "release": {
            "major": 45,
            "minor": 0,
            "patch": 0,
            "version": 1
        }
    },
    "libraries": [
        "/home/simon/Documents/Repositories/LSP/ZedScripts-VSCode/ZedScripts-LSP/tests/scripts"
    ]
}
data_local = {
    # "dataset": {
    #     "release": {
    #         "major": 42,
    #         "minor": 0,
    #         "patch": 0,
    #         "version": 1
    #     }
    # },
    "libraries": [
        "/home/simon/Zomboid"
    ]
}

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, ValidationError

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

    def test(self):
        return self.release

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


with open(Path(__file__).parent / "configuration_schema.json", "w", encoding="utf-8") as f:
    import json
    json.dump(ConfigurationModel.model_json_schema(), f, indent=4)


def format_validation_error(error: ValidationError) -> str:
    lines = []
    for issue in error.errors():
        path = ".".join(str(part) for part in issue["loc"]) or "<root>"
        lines.append(f"{path}: {issue['msg']}")
    return "\n".join(lines)


try:
    configuration = ConfigurationModel.model_validate(data_global)
    print(configuration)
except ValidationError as e:
    print("Failed to load configuration:")
    print(format_validation_error(e))

configuration = ConfigurationModel(dataset=DatasetModel())
print(configuration)





config_global = ConfigurationModel.model_validate(data_global)
config_local = ConfigurationModel.model_validate(data_local)

from typing import TypeVar
from pydantic import BaseModel
from deepmerge import always_merger

T = TypeVar("T", bound=BaseModel)


def merge_pydantic_models(base: T, nxt: T) -> T:
    """Merge two Pydantic model instances.

    The attributes of 'base' and 'nxt' that weren't explicitly set are dumped into dicts
    using '.model_dump(exclude_unset=True)', which are then merged using 'deepmerge',
    and the merged result is turned into a model instance using '.model_validate'.

    For attributes set on both 'base' and 'nxt', the value from 'nxt' will be used in
    the output result.

    @source: https://github.com/pydantic/pydantic/discussions/3416#discussioncomment-12267413
    """
    base_dict = base.model_dump(exclude_unset=True)
    nxt_dict = nxt.model_dump(exclude_unset=True)
    merged_dict = always_merger.merge(base_dict, nxt_dict)
    return base.model_validate(merged_dict)

print()
print(config_global)
print(config_local)
merged_config = merge_pydantic_models(config_global, config_local)
print(merged_config)

print()
print(merged_config.dataset)
print(merged_config.dataset.test())