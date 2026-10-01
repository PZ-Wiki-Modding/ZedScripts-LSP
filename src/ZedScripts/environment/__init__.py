import enum


class WorkspaceType(enum.StrEnum):
    """Represents different types of workspace folders."""
    LIBRARY = enum.auto()
    """A library defined by the user to reference things from.
    No validation should be performed on it."""
    PROJECT = enum.auto()
    """A workspace folder."""
    SOLITARY = enum.auto()
    """Files that are not opened as part of a workspace 
    or library but should still be validated.
    
    This workspace always exists and just holds solitary files."""

class VersionType(enum.StrEnum):
    """Represents different version types the workspace folders follow."""
    PRE_42 = enum.auto()
    """Modded pre-42 folder structure."""
    VERSIONING = enum.auto()
    """Modded versioning folder.
    
    https://pzwiki.net/wiki/Mod_structure#Common_and_versioning_folders"""
    COMMON = enum.auto()
    """Modded folder `common`.
    
    https://pzwiki.net/wiki/Mod_structure#Common_and_versioning_folders"""
    OTHER = enum.auto()
    """Other uncategorized version."""
    BASE_GAME = enum.auto()
    """Base game files (e.g., `ProjectZomboid/media`)."""

