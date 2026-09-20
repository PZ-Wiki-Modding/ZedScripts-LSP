from typing import TYPE_CHECKING

from lsprotocol import types

from ..utils import textrange_to_lsp

if TYPE_CHECKING:
    from ..structure.lexer import TextRange
    from ..scripts.dataset import Dataset
    from ..scripts.block import Block
    from ..scripts.value import Value

def make_hover_information(description: str, range: 'TextRange | None') -> types.Hover:
    return types.Hover(
        contents=types.MarkupContent(
            kind=types.MarkupKind.Markdown,
            value=description,
        ),
        range=textrange_to_lsp(range) if range is not None else None
    )