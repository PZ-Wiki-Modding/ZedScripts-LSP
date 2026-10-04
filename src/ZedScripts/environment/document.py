import hashlib
import logging
from pathlib import Path

from lsprotocol import types

from . import VersionType
from .version import Version
from ..utils import path_to_uri, position_to_texposition
from ..enums.Diagnostic import DiagnosticType
from ..structure.lexer import Lexer, TokenCollection
from ..structure.parser import parse_tokens, chunk_to_root
from ..providers import notifications
from ..providers.diagnostics import DiagnosticReport, WorkspaceDiagnosticReport, DiagnosticCollection
from ..providers.semantic_tokens import SemanticTokenCollection, build_syntactic_tokens
from ..providers.actions import make_linked_editing_ranges

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pathlib import Path

    from .workspace import Workspace
    from .mod import Mod
    from ..scripts.block import Root
    from ..scripts.dataset import Dataset

class Document:
    documents: list['Document'] = []
    documents_by_version: dict['Version', list['Document']] = {}
    def __init__(self, path: Path, rootType: str, workspace: 'Workspace', version: 'Version') -> None:
        self.rootType: str = rootType
        """The type of the root block of the document. If the document is not identified as a ZedScripts file,
        then this class should not be instantiated."""
        self.path: Path = path
        """The file system path to the document."""
        self.lexical_tokens: TokenCollection = TokenCollection()
        """Holds the lexical tokens of the document after lexing. That is, the raw tokens generated from the source text."""
        self.body: Root | None = None
        """Holds the root block of the document after parsing. None until properly parsed."""
        self.workspace: 'Workspace' = workspace
        """The workspace the document belongs to."""
        self.version: 'Version' = version
        """Holds the version type the document belongs to (versioning or common folder, base game etc)."""
        self.text: str | None = None
        """Holds the raw text content of the document. None until the text is read from the file
        or passed through Document.update_text."""

        self.mod: 'Mod | None' = None
        """The mod this document belongs to, if any."""

        self.semantic_tokens: SemanticTokenCollection = SemanticTokenCollection(self)
        """Holds semantic tokens for general highlighting. Populated from the validation process.
        
        Without the validation process, this collection will not be populated so users
        will not receive any syntax highlights besides syntactic ones."""
        self.syntactic_semantic_tokens: SemanticTokenCollection = SemanticTokenCollection(self)
        """Holds semantic tokens for syntax highlighting, that is things like `{`, `}` and `,`.
        
        This is used to not repopulate this list everytime we revalidate the document."""

        self.diagnostics: DiagnosticCollection = DiagnosticCollection()
        """Holds general diagnostics for the document after validation."""
        self.syntactic_diagnostics: DiagnosticCollection = DiagnosticCollection()
        """Holds syntactic diagnostics for the document after parsing."""

        self._validation_version: int = 0
        """Simple identifier to keep track of the version of the document for validation purposes.
        Incremented anytime the document content changed."""
        self._needs_validation: bool = True
        """Indicates whether the document needs to be revalidated. If set to False,
        then the document doesn't have any reasons to be revalidated as its diagnostics and
        semantic tokens are up-to-date."""

        # cache document instance
        Document.documents.append(self)
        Document.documents_by_version.setdefault(self.version, []).append(self)

        self.parse()

    def __repr__(self) -> str:
        return f"Document(version={self.version}, workspace={self.workspace}, mod={self.mod}, path={self.path})"

    def set_mod(self, mod: 'Mod') -> None:
        self.mod = mod

    def make_zedscripts(self) -> None:
        notifications.send_notification(
            notifications.ZedNotification.SET_ZEDSCRIPTS,
            uri=self.get_uri()
        )

    def get_text(self) -> str:
        if self.text is None:
            self.text = self.path.read_text()
        return self.text

    def update_text(self, text: str) -> None:
        """Bump the version if it has changed."""
        if self.get_text() != text:
            self.text = text
            self.bump()

    def get_uri(self) -> str:
        return path_to_uri(self.path)
    
    def get_lsp_diagnostics(self) -> list[types.Diagnostic]:
        config = self.workspace.get_configuration()
        lsp_diagnostics = self.diagnostics.to_lsp(config) + self.syntactic_diagnostics.to_lsp(config)
        logging.debug(f"LSP Diagnostics for {self.get_uri()}: {len(lsp_diagnostics)}")
        return lsp_diagnostics


# document management

    @staticmethod
    def list_by_workspace() -> dict['Document', 'Workspace']:
        return {document: document.workspace for document in Document.documents}

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
    def make(dataset: 'Dataset', path: Path, workspace: 'Workspace') -> 'Document | None':
        # find the rootType of the document
        rootType = dataset.test_for_root(path)
        if rootType is None:
            return None

        # find the version and skip if pre 42
        # since we don't validate that
        version = Version.find_or_make_version(path)
        if version.type == VersionType.PRE_42:
            return None

        logging.debug(f"Creating document for path: {path}, rootType: {rootType}, version: {version}")

        # if it is a valid ZedScripts document, create a new Document instance
        document = Document(path, rootType, workspace, version)
        document.make_zedscripts()
        Document.documents.append(document)

        return document

    @staticmethod
    def find_or_make(dataset: 'Dataset', path: Path, workspace: 'Workspace') -> 'Document | None':
        # if we find one, we don't have to verify it is a ZedScripts file
        # bcs it means the document didn't move
        document = Document.find(path)
        if document is None:
            document = Document.make(dataset, path, workspace)
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
    def rename(old_path: Path, new_path: Path) -> None:
        # no previous document exists for the old path
        document = Document.find(old_path)
        if document is None:
            return

        # first make sure that the new path is a valid root in the dataset
        rootType = document.workspace.dataset.test_for_root(new_path)
        if rootType is None:
            Document.delete(old_path)
            return

        # update the document information with new path and new root type
        document.path = new_path
        document.rootType = rootType
        document.make_zedscripts()



# this should mostly all be handled by the parser, to automatically mark files
# as having been reparsed, only if tokens changed

    def mark_changed(self) -> None:
        self._needs_validation = True
    def clear_changed(self) -> None:
        self._needs_validation = False
    def has_changed(self) -> bool:
        if self._needs_validation:
            return True
        return self.body is None

    def bump(self) -> None:
        """
        Increment the document version and mark it as needing validation.
        This version is used as an identifier for the diagnostic reports.
        """
        self._validation_version += 1
        self.mark_changed()

        # reset all diagnostics and tokens
        self.diagnostics.clear()
        self.syntactic_diagnostics.clear()
        self.semantic_tokens.clear()
        self.syntactic_semantic_tokens.clear()

        logging.debug("Bumped document version to %d", self._validation_version)

    def get_diagnostics_id(self) -> str:
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

    def get_semantic_tokens_id(self) -> str:
        """
        Generate a result ID based on the hash of the semantic tokens.
        This ensures that if tokens don't change (even if text changes),
        the client knows to skip processing via the "unchanged" report.
        """
        # Create a deterministic hash of the current semantic tokens
        tokens_str = str(sorted([
            (t.type.value, t.range) 
            for t in self.semantic_tokens
        ]))
        return hashlib.md5(tokens_str.encode()).hexdigest()



# notification response

    def parse(self) -> None:
        """
        Parse the new document text and update its syntactic structure and diagnostics.

        Args:
            text (str): The new text content of the document.
        """
        logging.debug("Parsing document: %s", self.get_uri())
        # tokenize and parse the document text
        self.lexical_tokens = Lexer.tokenize(self.get_text())
        result = parse_tokens(self.lexical_tokens)

        # set new syntactic diagnostics
        syntactic_diagnostics = self.syntactic_diagnostics
        syntactic_diagnostics.clear() # reset previous syntactic diagnostics
        config = self.workspace.configuration
        for error in result.errors:
            syntactic_diagnostics.add(
                config,
                type=DiagnosticType(error.type),
                location=error.location
            )

        # reparse the document body into a block structure for easier diagnostics
        self.body = chunk_to_root(self, result.chunk, self.rootType)
        build_syntactic_tokens(self)

    def validate(self) -> None:
        logging.debug("Validating document: %s", self.get_uri())
        # clear old diagnostics and semantic tokens
        self.diagnostics.clear()
        self.semantic_tokens.clear()

        # retrieve the starting point for validation
        body = self.body
        assert body is not None, f"Document ({self.get_uri()}) body should not be None before validation"

        # validate the root block, which will validate its children
        body.validate(self.workspace.dataset)



    def on_document_changed(self, text: str) -> None:
        self.update_text(text)

        if not self.has_changed():
            logging.debug("Document was not changed, skipping revalidation.")
            return
        self.clear_changed()

        # reparse
        logging.debug("Reparsing document: %s", self.get_uri())
        self.parse()

    def on_document_diagnostics(self, previous_result_id: str | None) -> DiagnosticReport:
        # validate the document
        self.validate()

        result_id = self.get_diagnostics_id()
        if (previous_result_id is not None
            and previous_result_id == result_id):
            return types.UnchangedDocumentDiagnosticReport(result_id)

        return types.FullDocumentDiagnosticReport(
            items=self.get_lsp_diagnostics(),
            result_id=result_id)

    def on_workspace_diagnostics(self, previous_result_id: str | None) -> WorkspaceDiagnosticReport:
        self.validate()

        # verify that the diagnostics didn't move
        # and if they didn't then send an unchanged report
        result_id = self.get_diagnostics_id()
        if (previous_result_id is not None
            and previous_result_id == result_id):
            return types.WorkspaceUnchangedDocumentDiagnosticReport(
                uri=self.get_uri(),
                result_id=result_id,
            )

        return types.WorkspaceFullDocumentDiagnosticReport(
            uri=self.get_uri(),
            items=self.get_lsp_diagnostics(),
            result_id=result_id,
        )

    def on_semantic_tokens(self) -> types.SemanticTokens:
        return types.SemanticTokens(
            data=SemanticTokenCollection(self, *(self.semantic_tokens + self.syntactic_semantic_tokens)).to_lsp(),
            result_id=self.get_semantic_tokens_id(), # useless since they don't send it back ?
        )

    def on_hover(self, position: types.Position) -> types.Hover | None:
        text_position = position_to_texposition(position)
        if self.body is None:
            return None
        return self.body.get_hover_information(self.workspace.dataset, text_position)

    def on_linked_editing_range(self, position: types.Position) -> types.LinkedEditingRanges | None:
        if self.body is None:
            return None
        text_position = position_to_texposition(position)
        
        root = self.body
        element = root.get_element_at(text_position)
        if element is not None:
            ranges = element.get_linked_editing_ranges(text_position)
            if ranges is None:
                return None
            return make_linked_editing_ranges(ranges)
        return None

    def on_definition(self, position: types.Position) -> list[types.LocationLink] | None:
        if self.body is None:
            return None
        text_position = position_to_texposition(position)

        root = self.body
        element = root.get_element_at(text_position)
        if element is not None:
            return element.get_definition(text_position)
        return None
