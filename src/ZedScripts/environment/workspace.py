import logging
import json
import re
from pathlib import Path
from typing import Any, TYPE_CHECKING, Iterable
from pydantic import ValidationError


from .. import CONFIGURATION_FILE_NAME, GLOBAL_CONFIGURATION_FILE
from . import WorkspaceType, VersionType
from .document import Document
from .mod import Mod, ModCollection
from .version import Version
from .config import ConfigurationModel
from ..providers import notifications
from ..utils import merge_pydantic_models, path_to_uri
from ..scripts.dataset import Dataset

if TYPE_CHECKING:
    from ..scripts.block import ScriptBlock



class Workspace:
    workspace_cache: dict[WorkspaceType, dict[Path, 'Workspace']] = {}
    global_configuration: ConfigurationModel | None = None
    global_dataset: 'Dataset' = Dataset()

    def __init__(self, folder: Path, workspace_type: WorkspaceType):
        self.folder = folder
        self.workspace_type = workspace_type
        self.documents: dict[Path, Document] = {}

        self.mods: ModCollection = ModCollection()
        self.ignored_patterns: list[re.Pattern] = []
        self.configuration: ConfigurationModel = self.update_configuration()
        self.dataset: Dataset = Dataset()
        self.dataset.load(self.configuration.dataset)

        # cache workspace
        Workspace.workspace_cache.setdefault(workspace_type, {})[folder] = self

    def __repr__(self) -> str:
        return f"Workspace(type={self.workspace_type}, folder={self.folder})"

    def load(self) -> tuple[int, int]:
        """
        Retrieve every script files and cache them as Document instances.

        Returns:
            tuple[int, int]: A tuple containing the number of loaded mods and the number of loaded documents.
        """
        logging.info(f"Loading workspace: {self.folder}")
        loaded_mod_count = self.load_mods()
        # self.load_documents()
        loaded_document_count = self.load_documents()
        return loaded_mod_count, loaded_document_count

    def load_documents(self) -> int:
        # inside the workspace folder, find every txt files, and try to load them
        # as documents
        files = list(self.folder.rglob("*.txt"))
        total_files = len(files)
        last_progress = 0
        step = 10
        step_count = step * total_files / 100
        loaded_file_count = 0
        for progress, path in enumerate(files):
            document = self.load_document(path)
            if document is not None:
                loaded_file_count += 1

            # send update notification to client
            if progress - last_progress >= step_count:
                logging.info(f"Loading progress: {progress}/{total_files}")
                notifications.send_notification(
                    notifications.ZedNotification.SET_PROGRESS,
                    progress=progress / total_files * 100,
                )
                last_progress = progress

        # send final progress notification
        notifications.send_notification(
            notifications.ZedNotification.SET_PROGRESS,
            progress=100
        )
        return loaded_file_count

    def load_mods(self) -> int:
        logging.info(f"Loading mods for workspace: {self.folder}")
        # look for mod.info files
        # one or more of these files are associated to a specific mod
        mod_count = 0
        for file in self.folder.rglob("mod.info"):
            # only consider versioning and common folders
            version = Version.find_or_make_version(file)
            if version.type in {VersionType.VERSIONING, VersionType.COMMON}:
                mod_folder = file.parent.parent # the folder containing the 42 / common folders
                mod = Mod.find_or_make_mod(mod_folder, self)
                mod.add_mod_info_file(file, version)
                self.mods[mod_folder] = mod
                mod_count += 1
                continue

            # if it's OTHER, then it's probably not a mod file
            # TODO: should we handle those ?

        return mod_count

    @staticmethod
    def load_libraries() -> int:
        logging.info("Loading libraries for all workspaces.")

        # gather libraries from configs
        config = Workspace.get_global_configuration()

        configs = []
        for workspace in Workspace.workspace_cache.get(WorkspaceType.PROJECT, {}).values():
            configs.append(workspace.get_configuration())
        merged_config = merge_pydantic_models(config, *configs)

        # add each libraries to global library cache
        libraries = merged_config.libraries
        libraries = Workspace.filter_out_projects(libraries)

        Workspace.workspace_cache[WorkspaceType.LIBRARY] = {}
        libraries_count = 0
        for library in libraries:
            Workspace.workspace_cache[WorkspaceType.LIBRARY][library] = Workspace(library, WorkspaceType.LIBRARY)
            libraries_count += 1

        notifications.send_notification(
            notifications.ZedNotification.SET_LIBRARIES_COUNT,
            count=libraries_count
        )

        for i, library in enumerate(Workspace.workspace_cache[WorkspaceType.LIBRARY].values()):
            notifications.send_notification(
                notifications.ZedNotification.LOADING_DOCUMENTS,
                uri=str(library.folder),
                workspace_type=library.workspace_type,
                index=i
            )
            library.load()
        return libraries_count

    def should_ignore(self, path: Path) -> bool:
        for pattern in self.ignored_patterns:
            if pattern.search(str(path)):
                return True
        return False

    def load_document(self, path: Path) -> Document | None:
        # skip if the path respects the ignored patterns
        if self.should_ignore(path):
            return None

        document = Document.find_or_make(self.dataset, path, self)
        if document is not None:
            self.mods.add_document(path, document)
            self.documents[path] = document
        return document


    @staticmethod
    def find_workspace(path: Path) -> 'Workspace | None':
        for workspaces in Workspace.workspace_cache.values():
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

    @staticmethod
    def filter_out_projects(libraries: set[Path]) -> set[Path]:
        """Filter out the libraries that are already present inside 
        folders of project workspaces since those will have already parsed that content.
        
        Doesn't filter out libraries that are a folder above a project workspace however."""
        project_folders = set(Workspace.workspace_cache.get(WorkspaceType.PROJECT, {}).keys())
        
        return {lib for lib in libraries 
                if not any(lib.resolve().is_relative_to(proj.resolve()) 
                           for proj in project_folders)}


# searches

    @staticmethod
    def search_for_block_references(version: Version, modules: Iterable[str], 
                                    id: str, block_type: str) -> list['ScriptBlock']:
        """Searches for block references within the specified modules and version context.

        Args:
            version (Version): The version context for the search.
            modules (Iterable[str]): List of module names to search within.
            id (str): ID of the block to search for.
            block_type (str): Expected type of the block to search for.
        """
        result: set['ScriptBlock'] = set()

        # skip search for pre B42 versions
        if version == Version.PRE_42:
            return list(result)

        # search into documents with a version that is general
        versions = [Version.COMMON, Version.BASE_GAME, Version.OTHER]
        documents = [doc for v in versions for doc in Document.documents_by_version.get(v, [])]
        for document in documents:
            if document.body is None: continue
            refs = document.body.find_references(modules, id, block_type)
            result.update(refs)

        # iterate over each mods, and look for the closest 
        # version to the version we are looking into for each
        # to look for references
        for workspaces in Workspace.workspace_cache.values():
            for workspace in workspaces.values():
                for mod in workspace.mods.values():
                    for document in mod.documents.values():
                        if document.body is None: continue
                        refs = document.body.find_references(modules, id, block_type)
                        result.update(refs)

        return list(result)




# configuration

    @staticmethod
    def find_workspace_of_configuration_file(path: Path) -> 'Workspace | None':
        # only search in project workspaces
        for workspace in Workspace.workspace_cache.get(WorkspaceType.PROJECT, {}).values():
            if (workspace.get_configuration_path() == path):
                return workspace
        return None

    @staticmethod
    def is_configuration_file(path: Path) -> bool:
        return path.is_file() and path.name == CONFIGURATION_FILE_NAME

    @staticmethod
    def is_global_configuration_file(path: Path) -> bool:
        return path.is_file() and path.resolve() == GLOBAL_CONFIGURATION_FILE

    @staticmethod
    def update_global_configuration(text: str | None = None) -> None:
        logging.info("Updating global configuration from %s", GLOBAL_CONFIGURATION_FILE)
        Workspace.global_configuration = Workspace.load_configuration(GLOBAL_CONFIGURATION_FILE, text=text)
        logging.debug(Workspace.global_configuration)

    @staticmethod
    def update_configuration_file(path: Path, text: str | None = None) -> bool:
        # skip if not a configuration file
        if not Workspace.is_configuration_file(path):
            return False

        # check if it's a global config file
        if Workspace.is_global_configuration_file(path):
            Workspace.update_global_configuration()
            return True

        # find out if it's a workspace-relative config file
        workspace = Workspace.find_workspace_of_configuration_file(path)
        if workspace is None:
            return False

        # if it's from a workspace, then we simply update its configuration
        workspace.update_configuration(text=text)
        return True

    @staticmethod
    def update_all_configurations() -> None:
        Workspace.update_global_configuration()
        for workspace in Workspace.workspace_cache.get(WorkspaceType.PROJECT, {}).values():
            workspace.update_configuration()

    def get_configuration_path(self) -> Path:
        return self.folder / CONFIGURATION_FILE_NAME

    def update_configuration(self, text: str | None = None) -> ConfigurationModel:
        logging.info("Updating configuration for workspace at %s", self.folder)
        self.configuration = Workspace.load_configuration(self.get_configuration_path(), text=text)
        logging.debug(self.configuration)
        self.post_update_configuration()
        return self.configuration

    def post_update_configuration(self) -> None:
        ignored = self.get_configuration().ignored
        self.ignored_patterns = [re.compile(pattern) for pattern in ignored]

    @staticmethod
    def get_global_configuration() -> ConfigurationModel:
        if Workspace.global_configuration is None:
            Workspace.update_global_configuration()
        assert Workspace.global_configuration is not None # to make Pylance happy
        return Workspace.global_configuration

    def get_configuration(self) -> ConfigurationModel:
        if self.configuration is None:
            self.update_configuration()
        assert self.configuration is not None # to make Pylance happy

        # merge with global configuration
        global_config = Workspace.get_global_configuration()

        return merge_pydantic_models(global_config, self.configuration)

    @staticmethod
    def load_configuration(config_path: Path, text: str | None = None) -> ConfigurationModel:
        if not config_path.exists() or not config_path.is_file():
            return ConfigurationModel()

        # load the configuration file
        try:
            if text is not None:
                data = json.loads(text)
            else:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
            logging.exception(f"Failed to load configuration file {config_path}. Loading default configuration.")
            return ConfigurationModel()

        try:
            # only validate a configuration file that is already a dictionary
            if isinstance(data, dict):
                return ConfigurationModel.model_validate(data)

            logging.warning(f"Configuration file {config_path} should contain a dictionary as the root. Loading default configuration.")
            return ConfigurationModel()
        except ValidationError as e:
            logging.warning(f"Configuration file validation error for {config_path}:\n{e}")
            return ConfigurationModel()
