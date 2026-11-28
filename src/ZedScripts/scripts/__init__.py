import enum
from types import UnionType
from typing import (get_args, get_origin,
                    Any, Literal, Union,
                    TypeVar, Generic)

from pz_scripts_data.schema import (
    ParameterMainType,
    FileType,
    TranslationType,
    CallBackType,
    BlockType,
    ObjectType,
    ArrayType,
)

from ..enums.Diagnostic import DiagnosticType


## key-value types

class ValueType(enum.StrEnum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    BLOCK = "block"
    CALLBACK = "callback"
    TRANSLATION = "translation"
    FILE = "file"

_early_return = (
    Literal['string']
    | ArrayType
    | ObjectType
    | BlockType
    | CallBackType
    | TranslationType
    | FileType
)

def _accepted_values(t) -> set:
    """Collects the concrete value types accepted by `t`, which can be a plain value (e.g. "float"), a Literal, or a union of those."""
    if isinstance(t, str):
        return {str(t)}
    if get_origin(t) is Literal:
        return set(get_args(t))
    if get_origin(t) in (Union, UnionType):
        return set().union(*(_accepted_values(arg) for arg in get_args(t)))
    return set()

def is_valid_type(t, ty):
    """Verifies that the given value type `t` is valid according to the specified type `ty`."""
    values = _accepted_values(t)
    return bool(values) and values.issubset(_accepted_values(ty))

def cant_self_validate(value_type: ParameterMainType) -> bool:
    """Verifies whenever the provided value_type cannot be validated by the value itself."""
    return is_valid_type(value_type, _early_return)

## block and values base classes


NodeT = TypeVar("NodeT")


class Element(Generic[NodeT]):
    def __init__(self) -> None:
        super().__init__()
        self.node: NodeT
        """AST node of the element."""


class UnknownScriptBlockError(Exception):
    """Exception raised when trying to access block data that
    doesn't exist."""
    pass

## need validation


class NeedErrorResult:
    def __init__(self, diagnostic_type: DiagnosticType, args: dict[str, Any]={}):
        self.diagnostic_type: DiagnosticType = diagnostic_type
        self.args: dict[str, Any] = args
