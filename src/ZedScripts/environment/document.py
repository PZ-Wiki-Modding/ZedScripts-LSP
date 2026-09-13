import hashlib
import logging
from pathlib import Path

from lsprotocol import types

from ..utils import path_to_uri
from ..structure.lexer import Lexer, TokenCollection
from ..structure.parser import parse_tokens, chunk_to_block
from ..providers.diagnostics import DiagnosticInfo, DiagnosticType, DiagnosticReport, WorkspaceDiagnosticReport, DiagnosticCollection
from ..providers.notifications import ZedNotification, SetZedScriptsNotificationParams
from ..providers.semantic_tokens import SemanticTokenCollection, build_syntactic_tokens
from ..scripts.validate import validate

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pathlib import Path

    from ..server import ZedServer
    from ..structure.blocks import Block

class Document:
    documents: list['Document'] = []
    def __init__(self, path: Path, text: str, rootType: str) -> None:
        self.rootType: str = rootType
        self.path: Path = path
        self.text: str = text
        self.lexical_tokens: TokenCollection = TokenCollection()
        self.body: Block | None = None
        self.semantic_tokens: SemanticTokenCollection = SemanticTokenCollection(self)

        self.diagnostics: DiagnosticCollection = DiagnosticCollection()
        self.syntactic_diagnostics: DiagnosticCollection = DiagnosticCollection()

        self._version_: int = 0
        self._needs_validation: bool = True

    def make_zedscripts(self, server: 'ZedServer') -> None:
        server.send_notification(
            method=ZedNotification.SET_ZEDSCRIPTS,
            params=SetZedScriptsNotificationParams(
                uri=path_to_uri(self.path)
            )
        )

    def update_text(self, text: str) -> None:
        if self.text != text:
            self.text = text
            self.bump()

    def get_uri(self):
        return path_to_uri(self.path)
    
    def get_lsp_diagnostics(self) -> list[types.Diagnostic]:
        lsp_diagnostics = self.diagnostics.to_lsp() + self.syntactic_diagnostics.to_lsp()
        logging.debug(f"LSP Diagnostics for {self.get_uri()}: {len(lsp_diagnostics)}")
        return lsp_diagnostics


# document management

    @staticmethod
    def get_documents() -> list['Document']:
        return Document.documents

    @staticmethod
    def find(path: Path) -> 'Document | None':
        for document in Document.documents:
            if document.path == path:
                return document
        return None

    @staticmethod
    def make(server: 'ZedServer', path: Path, text: str) -> 'Document | None':
        # find the rootType of the document
        rootType = server.dataset.test_for_root(path)
        if rootType is None:
            return None

        # if it is a valid ZedScripts document, create a new Document instance
        logging.debug(f"Found valid ZedScripts root for {path}: {rootType}")
        document = Document(path, text, rootType)
        document.make_zedscripts(server)
        Document.documents.append(document)

        return document

    @staticmethod
    def find_or_make(server: 'ZedServer', path: Path, text: str) -> 'Document | None':
        # if we find one, we don't have to verify it is a ZedScripts file
        # bcs it means the document didn't move
        document = Document.find(path)
        if document is None:
            document = Document.make(server, path, text)
        return document

    @staticmethod
    def delete(path: Path) -> None:
        document = Document.find(path)
        if document is not None:
            Document.documents.remove(document)

            # TODO: there might be some diagnostics cleanup needed here
            # aka remove any diagnostics by the LSP associated with this
            # document

    @staticmethod
    def rename(server: 'ZedServer', old_path: Path, new_path: Path) -> None:
        # first make sure that the new path is a valid root in the dataset
        rootType = server.dataset.test_for_root(new_path)
        if rootType is None:
            Document.delete(old_path)
            return

        # update the document information with new path and new root type
        document = Document.find(old_path)
        if document is not None:
            document.path = new_path
            document.rootType = rootType
            document.make_zedscripts(server)



# this should mostly all be handled by the parser, to automatically mark files
# as having been reparsed, only if tokens changed

    def mark_changed(self) -> None:
        self._needs_validation = True
    def clear_changed(self) -> None:
        self._needs_validation = False
    def was_changed(self) -> bool:
        return self._needs_validation

    def bump(self) -> None:
        """
        Increment the document version and mark it as needing validation.
        This version is used as an identifier for the diagnostic reports.
        """
        self._version_ += 1
        self.mark_changed()
        self.diagnostics.clear()

    def get_id(self) -> str:
        """
        Generate a result ID based on the hash of the diagnostics.
        This ensures that if diagnostics don't change (even if text changes),
        the client knows to skip processing via the "unchanged" report.
        """
        # Create a deterministic hash of the current diagnostics
        diagnostics_str = str(sorted([
            (d.type.value, d.location, d.args) 
            for d in self.diagnostics + self.syntactic_diagnostics
        ]))
        return hashlib.md5(diagnostics_str.encode()).hexdigest()


# notification response

    def parse(self) -> None:
        # tokenize and parse the document text
        self.lexical_tokens = Lexer.tokenize(self.text)
        result = parse_tokens(self.lexical_tokens)

        # set new syntactic diagnostics
        syntactic_diagnostics = self.syntactic_diagnostics
        syntactic_diagnostics.clear() # reset previous syntactic diagnostics
        for error in result.errors:
            syntactic_diagnostics.append(
                DiagnosticInfo(
                    type=DiagnosticType(error.type),
                    location=error.location,
                    args={}
                )
            )

        # reparse the document body into a block structure for easier diagnostics
        self.body = chunk_to_block(result.chunk)
        self.semantic_tokens = build_syntactic_tokens(self)

    def validate(self) -> None:
        validate(self)

    def on_document_diagnostics(self, previous_result_id: str | None) -> DiagnosticReport:
        result_id = self.get_id()
        if (previous_result_id is not None
            and previous_result_id == result_id):
            return types.UnchangedDocumentDiagnosticReport(result_id)

        # should validate document here probably

        return types.FullDocumentDiagnosticReport(
            items=self.get_lsp_diagnostics(),
            result_id=result_id)

    def on_workspace_diagnostics(self, previous_result_id: str | None) -> WorkspaceDiagnosticReport:
        result_id = self.get_id()
        if (previous_result_id is not None
            and previous_result_id == result_id):
            return types.WorkspaceUnchangedDocumentDiagnosticReport(
                uri=self.get_uri(),
                result_id=result_id,
            )

        # should validate document here probably

        return types.WorkspaceFullDocumentDiagnosticReport(
            uri=self.get_uri(),
            items=self.get_lsp_diagnostics(),
            result_id=result_id,
        )

    def on_semantic_tokens(self) -> types.SemanticTokens:
        return types.SemanticTokens(
            data=self.semantic_tokens.to_lsp(),
            result_id=self.get_id(), # useless since they don't send it back ?
        )

