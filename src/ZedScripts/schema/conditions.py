from __future__ import annotations

from typing import ClassVar, Self

from zedscript import Block
from zedscript.schema import SchemaComparator, SchemaOperand


class SchemaComparatorEquals(SchemaComparator, identifier="=="):
    _instance: ClassVar[SchemaComparatorEquals | None] = None

    def __new__(cls, *args, **kwargs) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def compare(self, a: any, b: any) -> bool:
        return a == b


class SchemaOperandBlockId(SchemaOperand, identifier="blockId"):
    def value(self, block: Block) -> str:
        return block.id


class SchemaOperandParameter(SchemaOperand, identifier="parameter"):
    def __init__(self, /, name: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.name: str = name

    def value(self, block: Block) -> str | None:
        return block.get_value(self.name)


class SchemaOperandConst(SchemaOperand, identifier="const"):
    def __init__(self, /, value: any, **kwargs) -> None:
        super().__init__(**kwargs)
        self._value: any = value

    def value(self, block: Block) -> any:
        return self._value
