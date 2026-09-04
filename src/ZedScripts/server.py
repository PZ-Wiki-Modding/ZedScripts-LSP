import os
import logging
from pathlib import Path

from lsprotocol import types
from pygls.lsp.server import LanguageServer
from pygls.uris import from_fs_path, to_fs_path

import ZedScripts
from .__about__ import __version__
from .utils import range_to_lsp
from .environment.document import Document
from .structure.lexer import Lexer
from .structure.parser import parse_tokens, chunk_to_block
from .providers.diagnostics import Diagnostic, DiagnosticType, DiagnosticDefinition
from .providers.semantic_tokens import build_syntactic_tokens, SemanticTokensVisitor
from .providers.locale import Localizer

logger = logging.getLogger(__name__)

def uri_to_path(uri: str) -> Path:
    fs_path = to_fs_path(uri)
    if fs_path is None:
        raise ValueError(f"Cannot convert URI to file path: {uri}")
    return Path(fs_path)

def path_to_uri(path: Path) -> str:
    uri = from_fs_path(str(path))
    if uri is None:
        raise ValueError(f"Cannot convert file path to URI: {path}")
    return uri

class ZedServer(LanguageServer):
    def __init__(self):
        super().__init__("zedserver", __version__)
        self.documents: dict[Path, Document] = {}
        self.localiser: Localizer = Localizer()
        self.localiser.load_locale_file()

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

        # only handle file named "test.txt" for now
        if path.name != "test.txt":
            return

        # existing documents should be fully reparsed
        if self.documents.get(path) is not None:
            self.documents.pop(path)

        document = Document(path, text)
        self.documents[path] = document

        document.lexical_tokens = Lexer.tokenize(text)
        result = parse_tokens(document.lexical_tokens)
        for error in result.errors:
            document.diagnostics.append(
                Diagnostic(
                    type=DiagnosticType(error.type),
                    location=error.location,
                    args={}
                )
            )

        document.body = chunk_to_block(result.chunk)
        document.semantic_tokens = build_syntactic_tokens(document)

        # schema_result = validate_file(document.path, document.body, self.schemas)
        # visit_block(
        #     schema_result,
        #     DiagnosticsVisitor(document, SemanticTokensVisitor(document))
        # )

        diagnostics: list[types.Diagnostic] = []
        for diagnostic in document.diagnostics:
            definition = DiagnosticDefinition.by_type[diagnostic.type]

            # ensure that the correct arguments are always passed
            for name, arg_type in definition.args.items():
                assert name in diagnostic.args
                assert isinstance(diagnostic.args[name], arg_type)

            diagnostics.append(
                types.Diagnostic(
                    range=range_to_lsp(diagnostic.location),
                    message=self.localiser.localize_string(definition.type,
                                                           args=diagnostic.args),
                    severity=definition.severity,
                    source=ZedScripts.SOURCE,
                    code=definition.type.name,
                    tags=definition.tags,
                )
            )

        uri = path_to_uri(path)
        self.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(
                uri=uri,
                diagnostics=diagnostics
            )
        )

server = ZedServer()



## EVENT HANDLERS

@server.feature(types.INITIALIZE)
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
    return types.InitializeResult(
        capabilities=types.ServerCapabilities(
            # our diagnostics depend on other files
            # so we prefer to diagnostic the whole workspace
            # diagnostics could take a while for large workspaces
            # (i.e. the game files)
            diagnostic_provider=types.DiagnosticOptions(
                inter_file_dependencies=True,
                workspace_diagnostics=True,
                identifier=ZedScripts.IDENTIFIER,
                work_done_progress=True,
            ),



            # text_document_sync=types.TextDocumentSyncKind.Full,
            # hover_provider=True,
            # semantic_tokens_provider=types.SemanticTokensOptions(...),
        )
    )


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(server: ZedServer, params: types.DidOpenTextDocumentParams) -> None:
    # try:
    server.document_changed(uri_to_path(params.text_document.uri), params.text_document.text)
    # except Exception:
    #     logger.exception("Error handling textDocument/didOpen")
    #     raise
    
@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(server: ZedServer, params: types.DidChangeTextDocumentParams) -> None:
    # try:
    document = server.workspace.get_text_document(params.text_document.uri)
    server.document_changed(uri_to_path(document.uri), str.join("", document.lines))
    # except Exception:
    #     logger.exception("Error handling textDocument/didChange")
    #     raise




## TODO

@server.feature(types.TEXT_DOCUMENT_HOVER)
def hover(server: ZedServer, params: types.HoverParams) -> types.Hover | None:
    # return hover info
    pass

@server.feature(types.TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL)
def semantic_tokens(server: ZedServer, params: types.SemanticTokensParams):
    # return semantic tokens
    pass
