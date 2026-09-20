from pathlib import Path
from typing import Iterable

from lsprotocol import types
from pygls.uris import from_fs_path, to_fs_path

from .structure.lexer import TextRange, TextPosition


def texrange_to_lsp(range: TextRange) -> types.Range:
    return types.Range(
        types.Position(range.start.line, range.start.offset),
        types.Position(range.end.line, range.end.offset)
    )
def position_to_texposition(position: types.Position) -> TextPosition:
    return TextPosition(position.line, position.character)

def uri_to_path(uri: str) -> Path:
    fs_path = to_fs_path(uri)
    if fs_path is None:
        raise ValueError(f"Cannot convert URI to file path: {uri}")
    return Path(fs_path)

def path_to_uri(path: Path | str) -> str:
    uri = from_fs_path(str(path))
    if uri is None:
        raise ValueError(f"Cannot convert file path to URI: {path}")
    return uri



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



def glob_files_by_extensions(folder: Path, extensions: set[str]) -> Iterable[Path]:
    """
    Glob all files in the given folder and its subfolders 
    that have one of the specified extensions.
    https://stackoverflow.com/a/57054058/33113221
    """
    files = (p.resolve() for p in Path(folder).rglob("*") if p.suffix in extensions)
    return files

