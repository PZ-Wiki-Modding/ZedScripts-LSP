import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict
from pprint import pformat

from .. import SCRIPTS_BLOCKS_DATA_LINK, ROOTS_DATA_LINK
from . import ScriptBlockData, ScriptBlockParameter, ValueType, cant_self_validate
from .version import GameVersion, DataVersion
from .. import SCRIPTS_DATA_MANIFEST
from ..providers.http import load_json
from ..environment.config import DatasetModel, DatasetTag

if TYPE_CHECKING:
    from ..environment.config import ReleaseModel


class Release(TypedDict):
    date: str
    version: int

class Datasets(TypedDict):
    blocks: str
    roots: str



class Manifest:
    instance: 'Manifest | None' = None

    def __init__(self, latest_build: GameVersion, releases: dict[GameVersion, Release], stable: DataVersion):
        self.latest_build:  GameVersion                = latest_build
        self.releases:      dict[GameVersion, Release] = releases
        self.stable:        DataVersion                = stable

        self.releases_list: list[str] = self.make_releases_list()

        # cache manifest
        Manifest.instance = self

    def __repr__(self) -> str:
        return f"Manifest(latest_build={self.latest_build}, releases={len(self.releases)}, stable={self.stable})"

    def make_releases_list(self) -> list[str]:
        """Transforms into a list of strings all available dataset versions."""
        releases_list: list[str] = []
        for version, release in self.releases.items():
            for v in range(release['version']):
                releases_list.append(str(version.to_data_version(v)))
        return sorted(releases_list)

    @staticmethod
    def from_dict(data: dict) -> "Manifest":
        return Manifest(
            latest_build=GameVersion.find_or_make(data["latest_build"]),
            releases={GameVersion.find_or_make(k): v for k, v in data["releases"].items()},
            stable=DataVersion(data["stable"]),
        )

    @staticmethod
    def find_release(game_version: GameVersion) -> Release | None:
        assert Manifest.instance is not None
        for version, release in Manifest.instance.releases.items():
            if version == game_version:
                return release
        return None

    @staticmethod
    def get_latest_version(major: int, minor: int, patch: int) -> int:
        assert Manifest.instance is not None
        release = Manifest.find_release(GameVersion.from_values(major, minor, patch))
        if release is None:
            raise ValueError(f"No release found for version {major}.{minor}.{patch}")
        return release['version']

    @staticmethod
    def from_release_model(dataset_config: 'ReleaseModel') -> 'DataVersion':
        game_version = GameVersion.from_values(dataset_config.major, dataset_config.minor, dataset_config.patch)
        version = dataset_config.version
        if version is None:
            version = Manifest.get_latest_version(dataset_config.major, dataset_config.minor, dataset_config.patch)
        data_version = game_version.to_data_version(version)
        return data_version



    @staticmethod
    def load() -> "Manifest":
        # if for some reason the LSP gets active a long time
        # this will not get updated (but tbh this should absolutely not be a problem)
        if Manifest.instance is not None:
            return Manifest.instance

        # load the manifest from the JSON file
        logging.info("Loading manifest...")
        manifest_data = load_json(SCRIPTS_DATA_MANIFEST)
        if manifest_data is None:
            raise RuntimeError("Failed to load manifest data")
        
        logging.debug(pformat(manifest_data))
        return Manifest.from_dict(manifest_data)

    def get_latest(self) -> tuple[DataVersion,Release]:
        versions = sorted(self.releases.keys())
        latest_version = versions[-1]
        release = self.releases[latest_version]
        return latest_version.to_data_version(release['version']), release

    def get_stable(self) -> DataVersion:
        stable_version = self.stable
        return stable_version


    def get_best_dataset_tag(self, key: DataVersion | DatasetTag) -> DataVersion:
        # find classic keyword cases
        match key:
            case DatasetTag.LATEST:
                return self.get_latest()[0]
            case DatasetTag.STABLE:
                return self.get_stable()
            case _:
                if not isinstance(key, DataVersion):
                    return NotImplemented

        # try to find the key in available releases
        to_find = str(key)
        releases_list = self.releases_list

        pos: int | None = releases_list.index(to_find) if to_find in releases_list else None
        if pos is not None:
            return DataVersion(releases_list[pos])

        # if not found, return stable
        logging.warning("Dataset version not found, falling back to stable.")
        return self.get_stable()



    def get_dataset_links(self, dataset_config: DatasetModel) -> Datasets:
        """
        Retrieve the dataset links for the specified tag_key.
        """
        key = dataset_config.to_data_version()
        best_tag = self.get_best_dataset_tag(key)
        if best_tag is None:
            raise ValueError(f"No dataset found for key: {key}")

        return {
            "blocks": SCRIPTS_BLOCKS_DATA_LINK.format(best_tag=best_tag),
            "roots": ROOTS_DATA_LINK.format(best_tag=best_tag),
        }






class Dataset:
    def __init__(self):
        self.manifest: Manifest = Manifest.load()

        self.blocks: dict[str, ScriptBlockData]
        self.roots: dict[str, ScriptBlockData]

    def __repr__(self) -> str:
        return f"Dataset(manifest={self.manifest}, blocks={len(self.blocks)}, roots={len(self.roots)})"

    def load(self, dataset_config: DatasetModel = DatasetModel()) -> None:
        logging.info(f"Loading dataset... ({dataset_config})")
        links = self.manifest.get_dataset_links(dataset_config)

        logging.info(f"Downloading from following dataset links:")
        logging.info(f"Blocks: {links['blocks']}")
        logging.info(f"Roots: {links['roots']}")

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
        for rootFile in self.roots.values():
            patterns = rootFile.get('pattern', [])
            for pattern in patterns:
                regex = re.compile(pattern)
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

    def get_block_tree(self, type: str) -> list[str]:
        """
        Retrieve the variantOf tree of the specified script block type.

        Args:
            type (str): The type of the script block to retrieve the tree for.

        Returns:
            list[str]: A list representing the hierarchical tree of the script block type.
        """
        block_data = self.get_script_block_data(type)
        assert block_data is not None, f"{type} block should be validated before retrieving its tree"

        # if it's a variant of another block then include that 
        # block's tree before the current block's type in the tree
        variant_of = block_data.get('variantOf')
        variant_tree = [type]
        if variant_of is not None:
            variant_tree = self.get_block_tree(variant_of) + variant_tree

        return variant_tree            

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

        return self.test_for_type(expected_type, value)

    def test_for_type(self, expected_type: ValueType, value: str) -> ValueType:
        #   return early types we can't really determine from the value itself
        if cant_self_validate(expected_type):
            return expected_type

        # check if boolean
        if value.lower() in ["true", "false"]:
            return ValueType.BOOLEAN

        # check if float or integer
        try:
            float(value) # try to convert it

            # it means that our value is a float or an integer
            # so we need to distinguish between float and integer
            if "." in value:
                return ValueType.FLOAT

            # if the expected type is float, then it's a float
            # because floats are allowed to not contain dots 
            # (simply representing whole numbers)
            elif expected_type == ValueType.FLOAT:
                return ValueType.FLOAT

            # else then we are simply an integer number
            return ValueType.INTEGER
        except ValueError:
            pass

        # default to string if no other type matches
        return ValueType.STRING


        