from typing import TYPE_CHECKING
from pathlib import Path

from .version import Version

if TYPE_CHECKING:
    from .workspace import Workspace
    from .document import Document

class Mod:
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

class ModCollection(dict[Path, Mod]):
    def load_documents(self) -> None: ...
