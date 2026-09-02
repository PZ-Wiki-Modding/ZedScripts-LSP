from pathlib import Path
from typing import Iterable

from lsprotocol import types
from .structure.lexer import TextRange


def range_to_lsp(range: TextRange) -> types.Range:
    return types.Range(
        types.Position(range.start.line, range.start.offset),
        types.Position(range.end.line, range.end.offset)
    )


def sort_by_load_order(files: Iterable[Path]) -> Iterable[Path]:
    """
    Sorts an iterable of script paths into the order that the game would load them.
    :param files: List of script filepaths.
    :return: Sorted list of filepaths.
    """
    templates: list[Path] = []
    other: list[Path] = []

    for path in files:
        if path.name.startswith("template_"):
            templates.append(path)
        else:
            other.append(path)

    templates.sort()
    other.sort()

    return templates + other
