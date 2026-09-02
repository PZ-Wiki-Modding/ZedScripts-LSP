from __future__ import annotations

import enum
from dataclasses import dataclass

from . import SchemaType


@dataclass
class SchemaTypeString(SchemaType, basic="string"):
    pattern: str


@dataclass
class SchemaTypeFloat(SchemaType, basic="float"):
    min: float | None
    max: float | None


@dataclass
class SchemaTypeInteger(SchemaType, basic="integer"):
    min: int | None
    max: int | None


@dataclass
class SchemaTypeBoolean(SchemaType, basic="boolean"):
    pass


@dataclass
class SchemaTypeEnum(SchemaType, basic="enum"):
    @dataclass
    class Member:
        name: str
        description: str
    members: dict[str, SchemaTypeEnum.Member]
    repeatable: bool


@dataclass
class SchemaTypeList(SchemaType, basic="list"):
    type: SchemaType
    separator: str
    open: str
    close: str


@dataclass
class SchemaTypeSequence(SchemaType, basic="sequence"):
    @dataclass
    class Element:
        type: SchemaType
        name: str
        description: str
        optional: bool

    elements: list[SchemaTypeSequence.Element]
    separator: str
    ordered: bool
    repeatable: bool


class ShortReferenceType(enum.Enum):
    NONE = "none"
    BASE_ONLY = "baseOnly"
    BASE_FIRST = "baseFirst"
    SAME_MODULE_ONLY = "sameModuleOnly",
    SAME_MODULE_FIRST = "sameModuleFirst"
    SAME_MODULE_AND_IMPORTS = "sameModuleAndImports"

    def __init__(self, json_name: str) -> None:
        self.json_name: str = json_name

    @staticmethod
    def from_json_name(name: str) -> ShortReferenceType:
        for member in list(ShortReferenceType):
            if member.json_name == name:
                return member
        raise ValueError("Tried to load non-existent ShortReferenceType " + name)


@dataclass
class SchemaTypeReference(SchemaType, basic="reference"):
    group: str
    short_reference_type: ShortReferenceType
    allow_qualified_references: bool


@dataclass
class SchemaTypeConst(SchemaType, basic="const"):
    value: int | float | str | bool

