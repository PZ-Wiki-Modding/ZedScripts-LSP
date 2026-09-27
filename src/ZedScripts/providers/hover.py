from typing import TYPE_CHECKING

from lsprotocol import types

from ..utils import textrange_to_lsp

if TYPE_CHECKING:
    from ..structure.lexer import TextRange

def make_hover_information(description: str, range: 'TextRange | None' = None) -> types.Hover | None:
    if description == "":
        return None
    return types.Hover(
        contents=types.MarkupContent(
            kind=types.MarkupKind.Markdown,
            value=_format_description(description),
        ),
        range=textrange_to_lsp(range) if range is not None else None
    )

def format_tree(tree: str) -> str:
    return f"```zedserver\n{tree}\n```"

# TODO: this could possibly not work in other IDEs
def _format_description(description: str) -> str:
    """
    Format the description for hover information.
    The C++ code blocks which are used in the datasets for script blocks are
    replaced with proper zedscripts code blocks.

    Args:
        description (str): 

    Returns:
        str: 
    """
    return description.replace("```cpp", "```zedscripts")