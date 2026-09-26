import os
import typing
import logging
from pathlib import Path
from pprint import pformat

from lsprotocol import types
from pygls.lsp.server import LanguageServer
from pygls.protocol.language_server import LanguageServerProtocol
from pygls.uris import from_fs_path, to_fs_path

from .__about__ import __version__
from .utils import uri_to_path
from .environment import WorkspaceType
from .environment.workspace import Workspace, Document
from .providers.diagnostics import DiagnosticReport
from .providers.semantic_tokens import get_tokens
from .providers.locale import zedlocalizer
from .providers import capabilities
from .providers.notifications import ZedNotification, NotificationParams
from .scripts.dataset import Dataset



# for future implementation of custom protocol features
class ZedLanguageProtocole(LanguageServerProtocol): ...



class ZedServer(LanguageServer):
    def __init__(self):
        super().__init__(name="zedserver", version=__version__, protocol_cls=ZedLanguageProtocole)
        self.documents: dict[Path, Document] = {}
        zedlocalizer.load_locale_files()
        self.dataset: Dataset = Dataset()

    def send_notification(self, method: ZedNotification, params: NotificationParams | None = None) -> None:
        self.protocol.notify(
            method,
            params
        )

    # def send_request(self, method: str, )


    def wait_for_debug_client(self) -> None:
        import time
        from .providers.debug import wait_for_port_available, force_close_port
        try:
            import debugpy
        except ImportError:
            logging.error("debugpy is not installed. Debugging will not be available.")
            return

        debug_port = 5678
        debug_host = "localhost"
        
        # ensure the debug port is available
        if not wait_for_port_available(debug_port, debug_host):
            logging.error(f"Debug port {debug_port} is still in use after waiting. Attempting to bind anyway...")

            # probably a bad idea to do that
            # but realistically, we should only be the ones using that port
            force_close_port(debug_port)
            time.sleep(0.2)


        debugpy.listen((debug_host, debug_port))
        logging.debug(f"Waiting for debug client to attach on {debug_host}:{debug_port}...")
        debugpy.wait_for_client()  # blocks until the "Python: Attach" launch config connects
        logging.debug("Debug client attached.")


    def startup(self) -> None:
        logging.info("ZedServer starting up.")

        logging.debug("ZEDSCRIPTS_DEBUG_WAIT=%s", os.environ.get("ZEDSCRIPTS_DEBUG_WAIT"))
        if os.environ.get("ZEDSCRIPTS_DEBUG_WAIT") == "1":
            self.wait_for_debug_client()

        self.start_io()



    def on_document_changed(self, path: Path, text: str) -> None:
        # first check if the file is a zedscripts file
        document = Workspace.find_or_make(path)
        if document is None:
            return
        
        logging.debug("Document changed: %s\n%s", path, text)

        # update it
        document.on_document_changed(text)

    def on_document_deleted(self, path: Path) -> None:
        Document.delete(path)

    def on_document_renamed(self, old_file: Path, new_file: Path) -> None:
        Document.rename(self, old_file, new_file)

    def on_document_diagnostics(self, path: Path, previous_result_id: str | None) -> DiagnosticReport | None:
        document = Workspace.find_or_make(path)
        if document is None:
            return None
        return document.on_document_diagnostics(self, previous_result_id)

    def on_semantic_tokens(self, path: Path) -> types.SemanticTokens | None:
        document = Document.find(path)
        if document is None:
            return None
        return document.on_semantic_tokens()

    def on_document_hover(self, path: Path, position: types.Position) -> types.Hover | None:
        document = Document.find(path)
        if document is None:
            return None
        return document.on_hover(self, position)


zedserver = ZedServer()



## EVENT HANDLERS

@zedserver.feature(types.INITIALIZE)
def initialize(server: ZedServer, params: types.InitializeParams):
    """
    In here we handle the initialization of the server. For that we provide
    a set of rules and capabilities that the server supports.

    ### Diagnostics
    Our diagnostics depend on other files so we prefer to diagnostic 
    the whole workspace. They could take a while for large workspaces
    (i.e. the game files) so we want to provide feedback when it takes
    a while.
    """
    # this will store what the server can currently do
    capabilities.register_client_capabilities(params)

    # load the dataset
    server.dataset.load()

    # TODO: implement workspace loading starting from this
    logging.debug("Server workspace folders")
    logging.debug(server.workspace.folders)
    for folder in server.workspace.folders:
        ws = Workspace(server, uri_to_path(folder), WorkspaceType.PROJECT)
        ws.load()

    # from the above, we determine what the server capabilities should be
    return types.InitializeResult(
        capabilities=capabilities.get_server_capabilities(),
        server_info=types.ServerInfo(
            name="ZedScripts Language Server",
            version=__version__,
        )
    )


@zedserver.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(server: ZedServer, params: types.DidOpenTextDocumentParams) -> None:
    server.on_document_changed(uri_to_path(params.text_document.uri), params.text_document.text)
    
@zedserver.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(server: ZedServer, params: types.DidChangeTextDocumentParams) -> None:
    document = server.workspace.get_text_document(params.text_document.uri)
    server.on_document_changed(uri_to_path(document.uri), str.join("", document.lines))

@zedserver.feature(types.WORKSPACE_DID_DELETE_FILES)
def workspace_did_delete_files(server: ZedServer, params: types.DeleteFilesParams) -> None:
    for file in params.files:
        path = uri_to_path(file.uri)
        server.on_document_deleted(path)

@zedserver.feature(types.WORKSPACE_DID_RENAME_FILES)
def workspace_did_rename_files(server: ZedServer, params: types.RenameFilesParams) -> None:
    for file in params.files:
        old_path = uri_to_path(file.old_uri)
        new_path = uri_to_path(file.new_uri)
        server.on_document_renamed(old_path, new_path)



@zedserver.feature(types.TEXT_DOCUMENT_DIAGNOSTIC)
def diagnostic(server: ZedServer, params: types.DocumentDiagnosticParams) -> DiagnosticReport | None:
    path = uri_to_path(params.text_document.uri)
    return server.on_document_diagnostics(path, params.previous_result_id)



# sadly I'm not sure that implementation works as expected because the client constantly
# asks again and again for workspace diagnostics
# it also doesn't ask for diagnostics of non-opened documents
# 
# # also see when implementing the configuration file:
# # https://microsoft.github.io/language-server-protocol/specifications/lsp/3.18/specification/#diagnostic_refresh
# @zedserver.feature(types.WORKSPACE_DIAGNOSTIC)
# def workspace_diagnostic(server: ZedServer, params: types.WorkspaceDiagnosticParams):
#     """
#     Provides diagnostics for all documents in the workspace.
#     This is called when the client requests workspace-wide diagnostics.
#     """
#     logging.info("Workspace diagnostic requested.")

#     # map of previous result IDs by document URI
#     previous_result_ids = {item.uri: item.value for item in params.previous_result_ids}
#     logging.debug(pformat(previous_result_ids))

#     items: list[types.WorkspaceDocumentDiagnosticReport] = []
#     for document in Document.get_documents():
#         uri = document.get_uri()
#         previous_result_id = previous_result_ids.get(uri)
#         items.append(document.get_lsp_workspace_diagnostics(previous_result_id))

#     return types.WorkspaceDiagnosticReport(items=items)


token_types, token_modifiers = get_tokens()
@zedserver.feature(
        types.TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL,
        types.SemanticTokensLegend(
            token_types=token_types,
            token_modifiers=token_modifiers,
        )
    )
def semantic_tokens(server: ZedServer, params: types.SemanticTokensParams):
    path = uri_to_path(params.text_document.uri)
    return server.on_semantic_tokens(path)


@zedserver.feature(types.TEXT_DOCUMENT_HOVER)
def hover(server: ZedServer, params: types.HoverParams) -> types.Hover | None:
    path = uri_to_path(params.text_document.uri)
    return server.on_document_hover(path, params.position)




## TODO

# @zedserver.feature(types.TEXT_DOCUMENT_HOVER)
# def hover(server: ZedServer, params: types.HoverParams) -> types.Hover | None:
#     # return hover info
#     pass
