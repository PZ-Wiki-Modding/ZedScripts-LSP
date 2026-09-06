from pathlib import Path

from lsprotocol import types

from ..structure.lexer import TokenCollection
from ..providers.diagnostics import DiagnosticInfo, DiagnosticReport, DiagnosticCollection
from ..providers.semantic_tokens import tokens_to_lsp
from ..providers.notifications import ZedNotification, SetZedScriptsNotificationParams
from ..utils import path_to_uri

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pathlib import Path

    from ..server import ZedServer
    from ..structure.blocks import Block
    from ..providers.semantic_tokens import SemanticToken

class Document:
    documents: list['Document'] = []
    def __init__(self, path: Path, text: str) -> None:
        self.path: Path = path
        self.text: str = text
        self.lexical_tokens: TokenCollection = TokenCollection()
        self.body: Block | None = None
        self.semantic_tokens: list[SemanticToken] = []
        self.diagnostics: DiagnosticCollection = DiagnosticCollection()

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
    def make(server: 'ZedServer', path: Path, text: str) -> 'Document':
        document = Document(path, text)
        document.make_zedscripts(server)
        Document.documents.append(document)
        return document

    @staticmethod
    def make_or_find(server: 'ZedServer', path: Path, text: str) -> 'Document':
        document = Document.find(path)
        if document is None:
            document = Document.make(server, path, text)
        return document



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
        return str(self._version_)


    def get_lsp_diagnostic(self, 
            params: types.DocumentDiagnosticParams
        ) -> DiagnosticReport:

        previous_result_id = params.previous_result_id
        result_id = self.get_id()
        if (previous_result_id is not None
            and previous_result_id == result_id):
            return types.UnchangedDocumentDiagnosticReport(result_id)

        # should validate document here probably

        return types.FullDocumentDiagnosticReport(
            items=self.diagnostics.to_lsp(), 
            result_id=result_id)

    def get_lsp_semantic_tokens(self) -> types.SemanticTokens:
        return types.SemanticTokens(
            data=tokens_to_lsp(self),
            result_id=self.get_id(), # useless since they don't send it back ?
        )
