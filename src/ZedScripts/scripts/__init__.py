import enum
from typing import (TYPE_CHECKING, 
                    TypedDict, Literal, NotRequired, 
                    TypeVar, Generic)

if TYPE_CHECKING:
    from ..structure.ast import ValueNode, BlockNode, Chunk



class ScriptBlockData(TypedDict):
    """
    The data structure representing a script block.
    """
    name: str
    description: str
    shortDescription: NotRequired[str]
    needsChildren: NotRequired[list[str]]
    parents: list[str]
    ID: NotRequired['ScriptBlockID']
    parameters: dict[str, 'ScriptBlockParameter']
    # properties: #TODO
    variantOf: NotRequired[str]
    """if this block is a variant of another block, the name of the base block"""

    # those should basically be unused here now
    isRoot: NotRequired[bool]
    pattern: NotRequired[list[str]]
    """to be used as regex patterns for identification"""
    noComma: NotRequired[bool]
    """default is false"""

class ScriptBlockID(TypedDict):
    """
    Provides information about the ID of the block.
    """
    parentsWithout: NotRequired[list[str]]
    values: NotRequired[list[str]]
    asType: NotRequired[bool]
    canHaveSpace: NotRequired[bool]
    translation: NotRequired['TranslationProperties']


## key-value types

type ScriptBlockValue = str | int | float | bool
class ScriptBlockParameter(TypedDict):
    """
    Represents a parameter of a script block.
    """
    name: str
    description: NotRequired[str]
    allowedDuplicate: NotRequired[bool]
    canBeEmpty: NotRequired[bool]
    default: NotRequired[ScriptBlockValue | list]
    type: NotRequired['ParameterType']
    deprecated: NotRequired['DeprecatedInfo']
    values: NotRequired[list[ScriptBlockValue]]
    needs: NotRequired['ScriptBlockNeeds']


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

_early_return: set[ValueType] = {
    ValueType.STRING,
    ValueType.ARRAY,
    ValueType.OBJECT,
    ValueType.BLOCK,
    ValueType.CALLBACK,
    ValueType.TRANSLATION,
}

def cant_self_validate(value_type: ValueType) -> bool:
    """Verifies whenever the provided value_type cannot be validated by the value itself."""
    return value_type in _early_return


class ParameterType(TypedDict):
    main: ValueType
    array: NotRequired['ArrayType']
    object: NotRequired['ObjectType']
    block: NotRequired['BlockType']
    translation: NotRequired['TranslationProperties']
    callback: NotRequired['CallbackType']

class ArrayType(TypedDict):
    separator: str
    type: Literal[ValueType.STRING, ValueType.INTEGER, ValueType.FLOAT, ValueType.BOOLEAN]

class ObjectType(TypedDict):
    keyValueSeparator: str
    """the separator used to split the key and value"""
    keyType: Literal[ValueType.STRING, ValueType.INTEGER, ValueType.FLOAT, ValueType.BOOLEAN]
    valueType: Literal[ValueType.STRING, ValueType.INTEGER, ValueType.FLOAT, ValueType.BOOLEAN]
    pairsSeparator: str
    """the separator used to split different key-value pairs"""

class BlockType(TypedDict):
    name: str
    """the block type (e.g. "sound", "item", "model"...)"""
    fullType: NotRequired[bool]
    """if true, this should use the module to reference the block"""
    noAutoImport: NotRequired[bool]
    """if true, the will not automatically check its own parent block module when fullType is set to true"""

class CallbackType(TypedDict):
    parameters: list['CallbackParameter']
    returns: NotRequired[str]

class CallbackParameter(TypedDict):
    name: str
    type: str
    isJava: bool


class ScriptBlockNeeds(TypedDict):
    name: str
    """the dependent parameter"""
    values: NotRequired[list[ScriptBlockValue]]
    """list of possible values for the dependent parameter"""
    valueToType: NotRequired[dict[str, str]]
    """mapping from dependent parameter values to their types
    (for dynamic typing based on other parameter's value)"""

## extra metadata

class DeprecatedInfo(TypedDict):
    replacedBy: NotRequired[str]
    description: NotRequired[str]
    version: NotRequired[str]

class TranslationProperties(TypedDict):
    """
    Used to indicate translation properties to an element.
    For example a key=value pair where the value needs a specific translation key.
    """
    keyPattern: str
    sourceFile: str


## block and values base classes


NodeT = TypeVar("NodeT")


class Element(Generic[NodeT]):
    def __init__(self) -> None:
        super().__init__()
        self.node: NodeT
        """AST node of the element."""
