from typing import TYPE_CHECKING
from pathlib import Path

from . import VersionType
from .version import Version

if TYPE_CHECKING:
    from .workspace import Workspace
    from .document import Document

class Mod:
    """Represents a mod inside a specific workspace.
    
    It is generally used to easily manage and retrieve files associated to a specific version.
    Since different mod sources can have different versioning structure, we need to handle them
    independently from each others when searching for block references."""
    mods: dict[Path, 'Mod'] = {}
    def __init__(self, folder: Path, workspace: 'Workspace'):
        self.folder: Path = folder
        self.workspace: 'Workspace' = workspace
        self.documents: dict[Path, 'Document'] = {}
        self.mod_info_files: dict[Path, 'Version'] = {}

    def add_mod_info_file(self, path: Path, version: 'Version') -> None:
        self.mod_info_files[path] = version

    @staticmethod
    def find_or_make_mod(folder: Path, workspace: 'Workspace') -> 'Mod':
        folder = folder.resolve()
        for mod_folder, mod in Mod.mods.items():
            if folder.is_relative_to(mod_folder):
                return mod
        mod = Mod(folder, workspace)
        Mod.mods[folder] = mod
        return mod

    def get_by_version(self) -> dict[Version, list['Document']]:
        """Retrieve documents grouped by their version."""
        result: dict[Version, list['Document']] = {}
        for doc in self.documents.values():
            result.setdefault(doc.version, []).append(doc)
        return result

    def get_closest_from_version(self, version: 'Version') -> list['Document']:
        """Retrieve the documents of the closest version equal or below of the provided version."""
        # only keep versions that use versioning
        by_version = self.get_by_version()
        versions = by_version.keys()
        versions_filtered = [v for v in versions if v.type == VersionType.VERSIONING]
        
        closest_version = version.find_closest_below(versions_filtered)
        if closest_version is None:
            return []
        return by_version[closest_version]


class ModCollection(dict[Path, Mod]):
    def add_document(self, path: Path, document: 'Document') -> None:
        for mod_path, mod in self.items():
            if path.is_relative_to(mod_path):
                mod.documents[path] = document
                return
