import enum
from typing import TypedDict, Optional, Literal

class ScriptBlockData(TypedDict):
    """
    The data structure representing a script block.
    """
    name: str
    description: str
    shortDescription: Optional[str]
    needsChildren: Optional[list[str]]
    parents: list[str]
    ID: 'ScriptBlockID'
    parameters: dict[str, 'ScriptBlockParameter']
    # properties: #TODO
    variantOf: Optional[str]
    """if this block is a variant of another block, the name of the base block"""

    # those should basically be unused here now
    isRoot: Optional[bool]
    pattern: Optional[list[str]]
    """to be used as regex patterns for identification"""
    noComma: Optional[bool]
    """default is false"""

class ScriptBlockID(TypedDict):
    """
    Provides information about the ID of the block.
    """
    parentsWithout: Optional[list[str]]
    values: Optional[list[str]]
    asType: Optional[bool]
    canHaveSpace: Optional[bool]
    translation: Optional['TranslationProperties']


## key-value types

type ScriptBlockValue = str | int | float | bool
class ScriptBlockParameter(TypedDict):
    """
    Represents a parameter of a script block.
    """
    name: str
    description: Optional[str]
    allowedDuplicate: Optional[bool]
    canBeEmpty: Optional[bool]
    default: Optional[ScriptBlockValue]
    type: Optional['ParameterType']
    deprecated: Optional['DeprecatedInfo']
    values: Optional[list[ScriptBlockValue]]
    needs: Optional['ScriptBlockNeeds']


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

class ParameterType(TypedDict):
    main: ValueType
    array: Optional['ArrayType']
    object: Optional['ObjectType']
    block: Optional['BlockType']
    translation: Optional['TranslationProperties']

class ArrayType(TypedDict):
    separator: str
    type: Literal[ValueType.STRING, ValueType.INTEGER, ValueType.FLOAT, ValueType.BOOLEAN]

class ObjectType(TypedDict):
    keyValueSep: str
    """the separator used to split the key and value"""
    keyType: Literal[ValueType.STRING, ValueType.INTEGER, ValueType.FLOAT, ValueType.BOOLEAN]
    valueType: Literal[ValueType.STRING, ValueType.INTEGER, ValueType.FLOAT, ValueType.BOOLEAN]
    pairsSeparator: str
    """the separator used to split different key-value pairs"""

class BlockType(TypedDict):
    name: str
    """the block type (e.g. "sound", "item", "model"...)"""
    fullType: Optional[bool]
    """if true, this should use the module to reference the block"""
    noAutoImport: Optional[bool]
    """if true, the will not automatically check its own parent block module when fullType is set to true"""


class ScriptBlockNeeds(TypedDict):
    name: str
    """the dependent parameter"""
    values: Optional[list[ScriptBlockValue]]
    """list of possible values for the dependent parameter"""
    valueToType: Optional[dict[str, str]]
    """mapping from dependent parameter values to their types
    (for dynamic typing based on other parameter's value)"""

## extra metadata

class DeprecatedInfo(TypedDict):
    replacedBy: Optional[str]
    description: Optional[str]
    version: Optional[str]

class TranslationProperties(TypedDict):
    """
    Used to indicate translation properties to an element.
    For example a key=value pair where the value needs a specific translation key.
    """
    keyPattern: str
    sourceFile: str