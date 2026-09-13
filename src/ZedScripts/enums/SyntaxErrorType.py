import enum

class SyntaxErrorType(enum.Enum):
    TOO_MANY_CLOSING_BRACKETS = enum.auto()
    BLOCK_MISSING_TYPE = enum.auto()
    BLOCK_NOT_CLOSED = enum.auto()
