from lsprotocol import types

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..structure.lexer import TextRange

def make_linked_editing_ranges(ranges: list['TextRange']) -> types.LinkedEditingRanges:
    # remove duplicate ranges
    ranges = list(set(ranges))
    
    # convert TextRange to types.Range
    r = [range.to_lsp() for range in ranges]
    return types.LinkedEditingRanges(ranges=r)
