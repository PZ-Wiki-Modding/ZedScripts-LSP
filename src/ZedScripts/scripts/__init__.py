import enum
from typing import (TYPE_CHECKING,  get_args,
                    TypedDict, Literal, NotRequired, 
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
    FILE = "file"

# _early_return: set[ValueType] = {
#     ValueType.STRING,
#     ValueType.ARRAY,
#     ValueType.OBJECT,
#     ValueType.BLOCK,
#     ValueType.CALLBACK,
#     ValueType.TRANSLATION,
# }

_early_return = (
    Literal['string']
    | ArrayType
    | ObjectType
    | BlockType
    | CallBackType
    | TranslationType
    | FileType
)

def is_valid_type(t, ty):
    """Verifies that the given value type `t` is valid according to the specified type `ty`."""
    return set(get_args(t)).issubset(get_args(ty))

def cant_self_validate(value_type: ParameterMainType) -> bool:
    """Verifies whenever the provided value_type cannot be validated by the value itself."""
    return is_valid_type(value_type, _early_return)


class ParameterType(TypedDict):
    main: ValueType
    array: NotRequired['ArrayTypeTEMP']
    object: NotRequired['ObjectTypeTEMP']
    block: NotRequired['BlockTypeTEMP']
    translation: NotRequired['TranslationProperties']
    callback: NotRequired['CallbackTypeTEMP']

class ArrayTypeTEMP(TypedDict):
    separator: str
    type: Literal[ValueType.STRING, ValueType.INTEGER, ValueType.FLOAT, ValueType.BOOLEAN]

class ObjectTypeTEMP(TypedDict):
    keyValueSeparator: str
    """the separator used to split the key and value"""
    keyType: Literal[ValueType.STRING, ValueType.INTEGER, ValueType.FLOAT, ValueType.BOOLEAN]
    valueType: Literal[ValueType.STRING, ValueType.INTEGER, ValueType.FLOAT, ValueType.BOOLEAN]
    pairsSeparator: str
    """the separator used to split different key-value pairs"""

class BlockTypeTEMP(TypedDict):
    name: str
    """the block type (e.g. "sound", "item", "model"...)"""
    fullType: NotRequired[bool]
    """if true, this should use the module to reference the block"""
    noAutoImport: NotRequired[bool]
    """if true, the will not automatically check its own parent block module when fullType is set to true"""

class CallbackTypeTEMP(TypedDict):
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
