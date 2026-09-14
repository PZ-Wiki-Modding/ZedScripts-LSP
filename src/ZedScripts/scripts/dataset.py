import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict
from pprint import pformat

from . import ScriptBlockData, ScriptBlockParameter, ValueType
from .. import SCRIPTS_DATA_MANIFEST
from ..providers.http import load_json


class Release(TypedDict):
    date: str
    version: int

class Datasets(TypedDict):
    blocks: str
    roots: str


class GameVersion:
    def __init__(self, version: str):
        self.version = version
        split_version = version.split(".")
        assert len(split_version) >= 3, "Version must have major, minor, and patch components"
        self.major = int(split_version[0])
        self.minor = int(split_version[1])
        self.patch = int(split_version[2])

    def __str__(self) -> str:
        return self.version

    def to_data_version(self, build: int) -> "DataVersion":
        return DataVersion(f"{self.major}.{self.minor}.{self.patch}.{build}")

    def __ge__(self, other):
        if not isinstance(other, GameVersion): return NotImplemented
        return (self.major, self.minor, self.patch) >= (other.major, other.minor, other.patch)

    def __gt__(self, other):
        if not isinstance(other, GameVersion): return NotImplemented
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)

    def __lt__(self, other):
        if not isinstance(other, GameVersion): return NotImplemented
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __le__(self, other):
        if not isinstance(other, GameVersion): return NotImplemented
        return (self.major, self.minor, self.patch) <= (other.major, other.minor, other.patch)

class DataVersion(GameVersion):
    def __init__(self, version: str):
        super().__init__(version)
        split_version = version.split(".")
        assert len(split_version) >= 4, "Data version must have major, minor, patch, and build components"
        self.build = int(split_version[3])

    def to_game_version(self) -> GameVersion:
        return GameVersion(f"{self.major}.{self.minor}.{self.patch}")



class Manifest:
    def __init__(self, latest_build: GameVersion, releases: dict[GameVersion, Release], stable: DataVersion):
        self.latest_build: GameVersion                = latest_build
        self.releases:     dict[GameVersion, Release] = releases
        self.stable:       DataVersion                = stable

    @staticmethod
    def from_dict(data: dict) -> "Manifest":
        return Manifest(
            latest_build=GameVersion(data["latest_build"]),
            releases={GameVersion(k): v for k, v in data["releases"].items()},
            stable=DataVersion(data["stable"]),
        )

    def get_latest(self) -> tuple[DataVersion,Release]:
        versions = sorted(self.releases.keys())
        latest_version = versions[-1]
        release = self.releases[latest_version]
        return latest_version.to_data_version(release['version']), release

    def get_stable(self) -> DataVersion:
        stable_version = self.stable
        return stable_version


    def get_best_dataset_tag(self, key: str) -> DataVersion | None:
        # find classic keyword cases        
        match key:
            case "latest":
                return self.get_latest()[0]

            case "stable":
                return self.get_stable()

        # else we handle the str as a version
        # and we find the closest one in the manifest
        return NotImplemented

    def get_dataset_links(self, key: str) -> Datasets:
        """
        Retrieve the dataset links for the specified tag_key.
        """
        best_tag = self.get_best_dataset_tag(key)
        if best_tag is None:
            raise ValueError(f"No dataset found for key: {key}")

        return {
            "blocks": f"https://raw.githubusercontent.com/PZ-Wiki-Modding/pz-scripts-data/refs/tags/{best_tag}/out/scriptsBlocks.json",
            "roots": f"https://raw.githubusercontent.com/PZ-Wiki-Modding/pz-scripts-data/refs/tags/{best_tag}/out/roots.json",
        }






class Dataset:
    def __init__(self):
        self.manifest: Manifest = self.load_manifest()

        self.blocks: dict[str, ScriptBlockData]
        self.roots: dict[str, ScriptBlockData]

    def load_manifest(self) -> Manifest:
        logging.info("Loading manifest...")
        manifest_data = load_json(SCRIPTS_DATA_MANIFEST)
        if manifest_data is None:
            raise RuntimeError("Failed to load manifest data")
        logging.debug(pformat(manifest_data))
        return Manifest.from_dict(manifest_data)

    def load(self) -> None:
        logging.info("Loading dataset...")
        links = self.manifest.get_dataset_links("latest")

        # load datasets (possibly from cache)
        blocks = load_json(links["blocks"])
        roots = load_json(links["roots"])

        logging.debug("Blocks JSON:")
        logging.debug(blocks)
        logging.debug("Roots JSON:")
        logging.debug(roots)

        # convert to proper type and store it
        self.blocks = {k.lower(): ScriptBlockData(v) for k, v in blocks.items()}
        self.roots = {k.lower(): ScriptBlockData(v) for k, v in roots.items()}

    def test_for_root(self, path: Path) -> str | None:
        """
        Determine the root type for the given file path based on the dataset's root patterns.

        Args:
            path (Path): The file path to test against the dataset's root patterns.

        Returns:
            str | None: The name of the root type if a matching pattern is found, otherwise None.
        """
        # the path is used to determine the root type
        # for that we need to resolve, normalize and use posix paths
        resolved_path = path.resolve().as_posix()

        # for each rootFile type, we test their identification patterns
        # to determine if the document is a zedscript doc
        logging.debug(f"Resolved path for testing: {resolved_path}")
        for rootFile in self.roots.values():
            patterns = rootFile.get('pattern', [])
            for pattern in patterns:
                regex = re.compile(pattern)
                logging.debug(f"Testing pattern {pattern}")
                if regex.search(resolved_path) is not None:
                    return rootFile['name']
        return None

    def is_script_block(self, type: str) -> bool:
        """
        Determine if the given type corresponds to a script block in the dataset.

        Args:
            type (str): The type to check against the dataset's script blocks.

        Returns:
            bool: True if the type corresponds to a script block, False otherwise.
        """
        return type.lower() in self.blocks.keys()

    def is_root(self, type: str) -> bool:
        """
        Determine if the given type corresponds to a root in the dataset.

        Args:
            type (str): The type to check against the dataset's roots.

        Returns:
            bool: True if the type corresponds to a root, False otherwise.
        """
        return type.lower() in self.roots.keys()

    def get_script_block_data(self, type: str) -> ScriptBlockData:
        """
        Retrieve the script block data for the given type from the dataset.
        You first need to verify that the type corresponds to a script block 
        or root in the dataset or the function will raise a ValueError.

        Args:
            type (str): The type of the script block or root to retrieve.

        Raises:
            ValueError: If the type does not correspond to a script block or root in the dataset.

        Returns:
            ScriptBlockData: The data associated with the specified script block or root type.
        """
        if self.is_script_block(type):
            return self.blocks[type.lower()]
        if self.is_root(type):
            return self.roots[type.lower()]
        raise ValueError(f"Script block data for type '{type}' not found")

    def can_block_have_parameter(self, type: str, parameter: str) -> bool:
        block_data = self.get_script_block_data(type)
        assert block_data is not None, f"{type} block should be validated before validating parameters"
        parameters = block_data.get('parameters', [])
        return parameter.lower() in parameters.keys()

    def get_parameter_data(self, type: str, parameter: str) -> ScriptBlockParameter:
        block_data = self.get_script_block_data(type)
        assert block_data is not None, f"{type} block should be validated before retrieving parameter data"
        parameters = block_data.get('parameters', {})
        return parameters[parameter.lower()]


    def get_parameter_type(self, value: str, parameter_data: ScriptBlockParameter) -> ValueType:
        """
        Determine the type of a parameter value based on its content and 
        the expected type specified in the parameter data.

        Args:
            value (str): The value of the parameter to determine the type for.
            parameter_data (ScriptBlockParameter): The metadata describing the expected type of the parameter.

        Raises:
            ValueError: If the expected type is an unsupported type from the dataset.

        Returns:
            ValueType: The determined type of the parameter value.
        """
        type_data = parameter_data.get('type')

        # default to string in any case
        if type_data is None:
            return ValueType.STRING

        expected_type = type_data['main']

        # assert type is something we know about
        if expected_type not in ValueType:
            raise ValueError(f"Unknown parameter type '{expected_type}'")

        # return early types we can't really determine from the value itself
        match expected_type:
            case ValueType.STRING:
                return ValueType.STRING
            case ValueType.ARRAY:
                return ValueType.ARRAY
            case ValueType.OBJECT:
                return ValueType.OBJECT
            case ValueType.BLOCK:
                return ValueType.BLOCK
            case ValueType.CALLBACK:
                return ValueType.CALLBACK
            case ValueType.TRANSLATION:
                return ValueType.TRANSLATION

        # check if boolean
        if value.lower() in ["true", "false"]:
            return ValueType.BOOLEAN

        # check if int
        elif value.isdigit():
            return ValueType.INTEGER

        # check if float
        try:
            float(value) # try to convert it

            # it means that our value is a float
            if "." in value:
                return ValueType.FLOAT

            # if the expected type is float
            elif expected_type == ValueType.FLOAT:
                return ValueType.FLOAT

            # else then we are simply an integer number
            return ValueType.INTEGER
        except ValueError:
            pass

        # default to string if no other type matches
        return ValueType.STRING


        