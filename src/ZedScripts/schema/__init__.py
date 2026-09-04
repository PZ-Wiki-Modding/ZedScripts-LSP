from __future__ import annotations

from dataclasses import dataclass
import abc
import enum
from typing import ClassVar, Any

from ..structure.blocks import Block


class IDType(enum.Enum):
    REQUIRED = enum.auto()
    OPTIONAL = enum.auto()
    NONE = enum.auto()


class SchemaOperand(abc.ABC):
    type_map: ClassVar[dict[str, type[SchemaOperand]]] = {}
    identifier: ClassVar[str]

    def __init_subclass__(cls, /, identifier: str, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        SchemaOperand.type_map[identifier] = cls
        setattr(cls, "identifier", identifier)

    def __init__(self, **kwargs) -> None: ...

    @abc.abstractmethod
    def value(self, block: Block) -> Any:
        """
        Returns the value of the operand.
        :param block: The block the condition is executing in.
        :return: Value of the operand.
        """
        pass


class SchemaComparator(abc.ABC):
    type_map: ClassVar[dict[str, type[SchemaComparator]]] = {}
    identifier: ClassVar[str]

    def __init_subclass__(cls, /, identifier: str, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        SchemaComparator.type_map[identifier] = cls
        setattr(cls, "identifier", identifier)

    @abc.abstractmethod
    def compare(self, a: Any, b: Any) -> bool:
        """
        Compares a against b.
        Comparators are not required to be commutative.
        :param a: The first operand to compare.
        :param b: The second operand to compare.
        :return: Result of the comparison.
        """
        pass


class SchemaCondition:
    def __init__(self, a: SchemaOperand, comparator: SchemaComparator, b: SchemaOperand) -> None:
        self.a: SchemaOperand = a
        self.comparator: SchemaComparator = comparator
        self.b: SchemaOperand = b

    def test(self, block: Block) -> bool:
        return self.comparator.compare(self.a.value(block), self.b.value(block))


@dataclass
class SchemaConditional:
    condition: SchemaCondition
    body: SchemaBlockBody


class SchemaType:
    type_map: ClassVar[dict[str, type[SchemaType]]] = {}
    basic: ClassVar[str]

    def __init_subclass__(cls, /, basic: str, **kwargs) -> None:
        cls.basic = basic
        SchemaType.type_map[basic] = cls


@dataclass
class SchemaParameter:
    type: SchemaType
    name: str
    description: str
    repeatable: bool
    default: str
    deprecated: bool


@dataclass
class SchemaValue:
    type: SchemaType
    name: str
    description: str
    minOccurrences: int
    maxOccurrences: int
    deprecated: bool


@dataclass
class SchemaBlockBody:
    parameters: dict[str, SchemaParameter]
    values: list[SchemaValue]
    blocks: dict[str, SchemaBlock]
    extra_parameters: bool
    required_parameters: list[str]
    required_blocks: list[str]
    conditionals: list[SchemaConditional]


@dataclass
class SchemaBlock:
    type: str
    description: str
    id_type: IDType
    reference_group: str
    valid_ids: list[str]
    repeatable: bool
    deprecated: bool
    body: SchemaBlockBody


@dataclass
class SchemaFile:
    valid_file_names: list[str]
    body: SchemaBlockBody
