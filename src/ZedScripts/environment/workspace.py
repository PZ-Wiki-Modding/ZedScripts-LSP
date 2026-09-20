import logging
from pathlib import Path
from typing import TYPE_CHECKING


from . import WorkspaceType
from .document import Document
from ..utils import glob_files_by_extensions

if TYPE_CHECKING:
    from ZedScripts.server import ZedServer





class Workspace:

    workspaceCache: dict[WorkspaceType, dict[Path, 'Workspace']] = {}

    def __init__(self, server: 'ZedServer', folder: Path, workspace_type: WorkspaceType):
        self.server = server
        self.folder = folder
        self.workspace_type = workspace_type
        self.documents: dict[Path, Document] = {}

        # cache workspace
        Workspace.workspaceCache.setdefault(workspace_type, {})[folder] = self



    def load(self) -> None:
        """
        Retrieve every script files and cache them as Document instances.
        """

        logging.info(f"Loading workspace: {self.folder}")
        # glob .txt and .info files
        for file in glob_files_by_extensions(self.folder, {".txt", ".info"}):
            logging.info(f"Found script file: {file}")

            # try to find or create a Document instance for this file
            # if it's not detected as a valid ZedScripts document then it will return None
            self.load_document(file)

    def load_document(self, path: Path) -> Document | None:
        document = Document.find_or_make(self.server, path, self)
        if document is not None:
            self.documents[path] = document
        return document

    @staticmethod
    def find_or_make(path: Path) -> Document | None:
        # find the document with the associated path
        docs = Document.get_by_workspace()
        for doc in docs.keys():
            if doc.path == path:
                return doc

        