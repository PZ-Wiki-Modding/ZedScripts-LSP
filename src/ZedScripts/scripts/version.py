from typing import TYPE_CHECKING, Self
if TYPE_CHECKING:
    from ..environment.config import ReleaseModel


class GameVersion:
    _cache: dict[str, 'GameVersion'] = {}
    def __init__(self, version: str):
        self.version = version
        split_version = version.split(".")
        assert len(split_version) >= 3, "Version must have major, minor, and patch components"
        self.major = int(split_version[0])
        self.minor = int(split_version[1])
        self.patch = int(split_version[2])

        # cache
        GameVersion._cache[version] = self

    def __hash__(self):
        return hash((self.major, self.minor, self.patch))

    def __str__(self) -> str:
        return self.version

    def to_data_version(self, build: int) -> "DataVersion":
        return DataVersion(f"{self.major}.{self.minor}.{self.patch}.{build}")

    @staticmethod
    def find_or_make(version: str) -> "GameVersion":
        return GameVersion._cache.get(version, GameVersion(version))

    @staticmethod
    def from_values(major: int, minor: int, patch: int) -> "GameVersion":
        return GameVersion.find_or_make(f"{major}.{minor}.{patch}")

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

    def __eq__(self, other):
        if not isinstance(other, GameVersion): return NotImplemented
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

class DataVersion(GameVersion):
    _data_cache: dict[str, 'DataVersion'] = {}
    def __init__(self, version: str):
        super().__init__(version)
        split_version = version.split(".")
        assert len(split_version) >= 4, "Data version must have major, minor, patch, and build components"
        self.build = int(split_version[3])

        # cache
        DataVersion._data_cache[version] = self

    def __hash__(self):
        return hash((self.major, self.minor, self.patch, self.build))

    def to_game_version(self) -> GameVersion:
        return GameVersion.find_or_make(f"{self.major}.{self.minor}.{self.patch}")

    @staticmethod
    def find_or_make(version: str) -> "DataVersion":
        return DataVersion._data_cache.get(version, DataVersion(version))