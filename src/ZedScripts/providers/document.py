from pathlib import Path

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pathlib import Path

    from ..structure.blocks import Block
    from ..structure.lexer import TokenCollection
    from .diagnostics import Diagnostic
    from .semantic_tokens import SemanticToken


class Document:
    def __init__(self, path: Path, text: str) -> None:
        self.path: Path = path
        self.text: str = text
        self.lexical_tokens: TokenCollection = TokenCollection()
        self.body: Block | None = None
        self.semantic_tokens: list[SemanticToken] = []
        self.diagnostics: list[Diagnostic] = []
