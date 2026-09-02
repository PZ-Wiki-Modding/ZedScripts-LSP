import logging
from pathlib import Path

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from ZedScripts.__about__ import __version__
from .workspace.document import Document
from .structure.lexer import Lexer
from .structure.parser import parse_tokens, chunk_to_block
from .providers.diagnostics import Diagnostic, DiagnosticType
from .providers.semantic_tokens import build_syntactic_tokens, SemanticTokensVisitor

def uri_to_path(uri: str) -> Path:
    return Path(uri.replace("%3A", ":"))

class ZedServer(LanguageServer):
    def __init__(self):
        super().__init__("zedserver", __version__)
        self.documents: dict[Path, Document] = {}

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

        schema_result = validate_file(document.path, document.body, self.schemas)
        visit_block(
            schema_result,
            DiagnosticsVisitor(document, SemanticTokensVisitor(document))
        )

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
                    message=self.localiser.localise_string(definition.type.name,
                                                           args=diagnostic.args),
                    severity=definition.severity
                )
            )

        self.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(
                uri=path.as_uri(),
                diagnostics=diagnostics
            )
        )

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

