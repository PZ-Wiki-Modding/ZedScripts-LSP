import logging
from typing import TypedDict
from pprint import pformat

from . import ScriptBlockData
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
        self.blocks = {k: ScriptBlockData(v) for k, v in blocks.items()}
        self.roots = {k: ScriptBlockData(v) for k, v in roots.items()}



