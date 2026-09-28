



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
