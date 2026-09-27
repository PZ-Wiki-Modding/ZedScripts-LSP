import logging
import re
from pathlib import Path

from . import VersionType



SCRIPT_FILE_VERSION_PATTERN = r"(?:(?P<base>\w+))\/(?:(?P<version>(?:4\d(?:\.\d+)*)|common)\/)?(?:(?P<media>media)|(?P<modinfo>mod\.info))"
"""
Pattern to match script file versions in the file path.

- The `base` is the folder before the versioning/common or media folder.
- The `version` is the folder containing the version number or the `common` folder. (can be absent)
- The `media` is the folder containing most modding files.
- The `modinfo` means the path is a `mod.info` file.
"""

_DEFAULT_MAJOR = 42
"""Default major version number"""
_DEFAULT_MINOR = 0
"""Default minor version number"""

class Version:
    # static instances
    COMMON: 'Version'
    # POST_42: 'Version' # that one is dynamic based on the source
    PRE_42: 'Version'
    OTHER: 'Version'
    """`Any` in old ZedScripts."""
    BASE_GAME: 'Version'

    key_format: str = "{type}.{major}.{minor}"
    version_map: dict[str, 'Version'] = {}

    def __init__(self, source: str):
        self.source: str = source
        type, major, minor = Version.get_type(source)
        self.type: VersionType = type
        self.major: int = major
        self.minor: int = minor

        self.version: str = Version.format_version(type, major, minor)
        Version.version_map[self.version] = self

    def __repr__(self) -> str:
        return f"Version(source={self.source}, type={self.type}, major={self.major}, minor={self.minor})"

    @staticmethod
    def format_version(type: VersionType, major: int, minor: int) -> str:
        """Format a version string for easy comparison and storage."""
        return Version.key_format.format(type=type, major=major, minor=minor)

    @staticmethod
    def get_type(source: str) -> tuple[VersionType, int, int]:
        # TODO: implement

        match source:
            case VersionType.COMMON:
                return VersionType.COMMON, _DEFAULT_MAJOR, _DEFAULT_MINOR
            case VersionType.PRE_42:
                return VersionType.PRE_42, _DEFAULT_MAJOR, _DEFAULT_MINOR
            case VersionType.OTHER:
                return VersionType.OTHER, _DEFAULT_MAJOR, _DEFAULT_MINOR
            case VersionType.BASE_GAME:
                return VersionType.BASE_GAME, _DEFAULT_MAJOR, _DEFAULT_MINOR

        # try to find the version based on the source string
        parts = source.split('.')
        if len(parts) == 0:
            logging.warning("Source string is empty.")
            return VersionType.OTHER, _DEFAULT_MAJOR, _DEFAULT_MINOR

        # try to convert to int the major part
        try:
            major = int(parts[0])
        except ValueError:
            logging.warning("Source string does not start with a valid integer.")
            return VersionType.OTHER, _DEFAULT_MAJOR, _DEFAULT_MINOR

        # values under 42 are just invalid and never handled by any version of the game
        if major < 42:
            logging.warning("Source string has a major version under 42, which is invalid.")
            return VersionType.OTHER, _DEFAULT_MAJOR, _DEFAULT_MINOR

        # retrieve the minor if present
        minor = 0
        if len(parts) > 1:
            try:
                minor = int(parts[1])
            except ValueError:
                logging.warning("Source string has an invalid minor version.")
                return VersionType.OTHER, _DEFAULT_MAJOR, _DEFAULT_MINOR

        # other values after minor are ignored by the game
        # so no need to retrieve those

        return VersionType.VERSIONING, major, minor

    @staticmethod
    def from_string(version_str: str) -> 'Version':
        """
        Convert a version string to a type, major and minor information and check if 
        the version string already exists in the version map, which will be returned.

        Else, a new Version instance will be created and returned.

        Args:
            version_str (str): The version string to be converted into a Version instance, 
                which comes from the file path usually.

        Returns:
            Version: The Version instance corresponding to the given version string.
        """
        type, major, minor = Version.get_type(version_str)
        key = Version.format_version(type, major, minor)
        if key in Version.version_map:
            return Version.version_map[key]
        return Version(version_str)


    @staticmethod
    def find_or_make_version(path: Path) -> 'Version':
        path_posix = path.as_posix()

        # try to match the version pattern in the path
        m = re.compile(SCRIPT_FILE_VERSION_PATTERN).search(path_posix)
        if not m or len(m.groupdict()) == 0:
            return Version.OTHER

        groups = m.groupdict()

        # try to match a version string in the path
        version_str = groups.get("version")
        if version_str:
            return Version.from_string(version_str)

        # verify if it is the PZ source folder which doesn't use versioning folders
        # linux uses projectzomboid while windows uses ProjectZomboid
        base = groups.get("base")
        if base in ["projectzomboid", "ProjectZomboid"]:
            # we can check that in the base folder there is a `projectzomboid.jar` 
            # file which would mean it is B42
            # using the match, we can retrieve the path of the base
            base_path = path_posix[:m.start() + len(base)]
            jar_path = Path(f"{base_path}/projectzomboid.jar")
            if jar_path.exists() and jar_path.is_file():
                return Version.BASE_GAME

        # else, we see if this is a B41 file
        # that is it has a media folder or it's a mod.info file
        if groups.get("media") or groups.get("modinfo"):
            return Version.PRE_42

        # we didn't find any indicator for a specific version
        return Version.OTHER

    def find_closest_below(self, others: list['Version']) -> 'Version | None':
        others_str = [str(other) for other in others]
        others_str.sort()

        # if self is not using versioning, then we simply retrieve the latest
        if self.type != VersionType.VERSIONING:
            return Version(others_str[-1])

        # check if it's itself in the list
        if str(self) in others_str:
            return self

        # we now insert self into the sorted list to find the closest below
        self_str = str(self)
        others_str.append(self_str)
        others_str.sort() # sort again of course

        # find self in the sorted list
        self_index = others_str.index(self_str)

        # if self is not the first element, then we return the element just before it
        if self_index > 0:
            return Version(others_str[self_index - 1])

        # if it's at the first position, we pick the version above
        # TODO: this is generally not a common case, probably should verify how
        # the game handles it
        if self_index == 0 and len(others_str) > 1:
            return Version(others_str[self_index + 1])

        logging.warning("No closest below version found for %s", self)

        # if we reach here, it means there is no closest below version
        return None
        
        

        



Version.COMMON = Version(VersionType.COMMON)
Version.PRE_42 = Version(VersionType.PRE_42)
Version.OTHER = Version(VersionType.OTHER)
Version.BASE_GAME = Version(VersionType.BASE_GAME)