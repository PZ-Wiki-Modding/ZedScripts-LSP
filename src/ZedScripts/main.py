import logging
from pathlib import Path

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from ZedScripts.__about__ import __version__

def uri_to_path(uri: str) -> Path:
    return Path(uri.replace("%3A", ":"))

class ZedServer(LanguageServer):
    def __init__(self):
        super().__init__("zedserver", __version__)

    def document_changed(self, path: Path, text: str) -> None:
        logging.debug("Document changed: %s\n%s", path, text)

server = ZedServer()

@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(server: ZedServer, params: types.DidOpenTextDocumentParams) -> None:
    server.document_changed(uri_to_path(params.text_document.uri), params.text_document.text)
    
@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(server: ZedServer, params: types.DidChangeTextDocumentParams) -> None:
    document = server.workspace.get_text_document(params.text_document.uri)
    server.document_changed(uri_to_path(document.uri), str.join("", document.lines))


if __name__ == "__main__":
    server.start_io()

