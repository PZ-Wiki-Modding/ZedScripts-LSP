import os
import logging
from pathlib import Path

from lsprotocol import types
from pygls.lsp.server import LanguageServer
from pygls.uris import from_fs_path, to_fs_path

import ZedScripts
from .__about__ import __version__
from .utils import uri_to_path
from .environment.document import Document
from .structure.lexer import Lexer
from .structure.parser import parse_tokens, chunk_to_block
from .providers.diagnostics import DiagnosticInfo, DiagnosticType
from .providers.semantic_tokens import build_syntactic_tokens, get_tokens
from .providers.locale import zedlocalizer
from .providers import capabilities

logger = logging.getLogger(__name__)

class ZedServer(LanguageServer):
    def __init__(self):
        super().__init__("zedserver", __version__)
        self.documents: dict[Path, Document] = {}
        zedlocalizer.load_locale_files()

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



    def document_changed(self, path: Path, text: str) -> None:
        logging.debug("Document changed: %s\n%s", path, text)

        document = Document.make_or_find(path, text)
        document.update_text(text)

        if not document.was_changed():
            logging.debug("Document was not changed, skipping revalidation.")
            return

        document.lexical_tokens = Lexer.tokenize(text)
        result = parse_tokens(document.lexical_tokens)
        for error in result.errors:
            document.diagnostics.append(
                DiagnosticInfo(
                    type=DiagnosticType(error.type),
                    location=error.location,
                    args={}
                )
            )

        document.body = chunk_to_block(result.chunk)
        document.semantic_tokens = build_syntactic_tokens(document)
        logging.debug(f"Token amount: {len(document.semantic_tokens)}")
        document.get_lsp_semantic_tokens()

        # logging.debug("Semantic tokens for document %s: %s", path, str(document.semantic_tokens))
        logging.debug("Made semantic tokens")


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
    server.document_changed(uri_to_path(params.text_document.uri), params.text_document.text)
    
@zedserver.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(server: ZedServer, params: types.DidChangeTextDocumentParams) -> None:
    document = server.workspace.get_text_document(params.text_document.uri)
    server.document_changed(uri_to_path(document.uri), str.join("", document.lines))


@zedserver.feature(types.TEXT_DOCUMENT_DIAGNOSTIC)
def diagnostic(server: ZedServer, params: types.DocumentDiagnosticParams):
    path = uri_to_path(params.text_document.uri)
    document = Document.find(path)
    if document is None:
        return
    return document.get_lsp_diagnostic(params)


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
    document = Document.find(path)
    if document is None:
        return
    return document.get_lsp_semantic_tokens()





## TODO

# @zedserver.feature(types.TEXT_DOCUMENT_HOVER)
# def hover(server: ZedServer, params: types.HoverParams) -> types.Hover | None:
#     # return hover info
#     pass
