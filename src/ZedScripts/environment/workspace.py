import logging
from pathlib import Path
from typing import TYPE_CHECKING


from . import WorkspaceType, VersionType
from .document import Document
from .mod import Mod, ModCollection
from .version import Version
from ..utils import glob_files_by_extensions

if TYPE_CHECKING:
    from ..server import ZedServer
    from ..scripts.block import Block




class Workspace:

    workspaceCache: dict[WorkspaceType, dict[Path, 'Workspace']] = {}

    def __init__(self, server: 'ZedServer', folder: Path, workspace_type: WorkspaceType):
        self.server = server
        self.folder = folder
        self.workspace_type = workspace_type
        self.documents: dict[Path, Document] = {}

        self.mods: ModCollection = ModCollection()

        # cache workspace
        Workspace.workspaceCache.setdefault(workspace_type, {})[folder] = self

    def load(self) -> None:
        """
        Retrieve every script files and cache them as Document instances.
        """
        logging.info(f"Loading workspace: {self.folder}")
        self.load_mods()
        self.load_documents()

    def load_documents(self) -> None:
        # glob .txt and .info files
        for file in glob_files_by_extensions(self.folder, {".txt", ".info"}):
            # try to find or create a Document instance for this file
            # if it's not detected as a valid ZedScripts document then it will return None
            self.load_document(file)

    def load_mods(self) -> None:
        logging.info(f"Loading mods for workspace: {self.folder}")
        # look for mod.info files
        # one or more of these files are associated to a specific mod
        for file in self.folder.rglob("mod.info"):
            # only consider versioning and common folders
            version = Version.find_or_make_version(file)
            if version.type in {VersionType.VERSIONING, VersionType.COMMON}:
                mod = Mod.find_or_make_mod(file.parent.parent, self)
                mod.add_mod_info_file(file, version)
                self.mods[file] = mod
                continue

            # if it's OTHER, then it's probably not a mod file
            # TODO: should we handle those ?


    def load_document(self, path: Path) -> Document | None:
        document = Document.find_or_make(self.server, path, self)
        if document is not None:
            mod = Mod.find_or_make_mod(path.parent, self)
            if mod is not None:
                document.set_mod(mod)
            self.documents[path] = document
        return document

    @staticmethod
    def find_workspace(path: Path) -> 'Workspace | None':
        for workspace_type, workspaces in Workspace.workspaceCache.items():
            for folder, workspace in workspaces.items():
                if folder in path.parents:
                    return workspace
        return None

    @staticmethod
    def find_or_make(path: Path) -> Document | None:
        # find the document with the associated path
        docs = Document.list_by_workspace()
        for doc in docs.keys():
            if doc.path == path:
                return doc

        workspace = Workspace.find_workspace(path)
        if workspace is not None:
            return workspace.load_document(path)
        return None


# searches

    @staticmethod
    def search_for_block_references(version: Version, modules: list[str], block: str, block_type: str) -> list['Block']:
        """_summary_

        Args:
            version (Version): The version context for the search.
            modules (list[str]): List of module names to search within.
            block (str): Name of the block to search for.
            block_type (str): Expected type of the block to search for.

        Returns:
            list[Block]: List of blocks that match the search criteria.
        """
        result: list['Block'] = []

        # skip search for pre B42 versions
        if version == Version.PRE_42:
            return result

        # iterate over each workspace, and look for the closest version setup
        # to the version we are looking into

        return NotImplemented