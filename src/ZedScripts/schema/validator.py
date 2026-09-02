from __future__ import annotations

import enum
import re
import typing
from functools import singledispatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from zedscript import Block
from zedscript.lexer import Token, TokenCollection
from zedscript.schema import SchemaFile, SchemaBlockBody, SchemaBlock, SchemaType, IDType
from zedscript.schema.types import SchemaTypeFloat, SchemaTypeInteger, SchemaTypeBoolean, SchemaTypeString, \
    SchemaTypeList, SchemaTypeEnum, SchemaTypeSequence, SchemaTypeReference, SchemaTypeConst
from zedscript.ast import BlockNode

PATTERN_FLOAT = re.compile("-?\\d+(?:\\.\\d+)?")
PATTERN_INTEGER = re.compile("-?\\d+")
PATTERN_ANY = re.compile(".+")
PATTERN_BOOLEAN = re.compile("^true|false$", re.IGNORECASE)


class SchemaError(enum.Enum):
    UNKNOWN_PARAMETER = enum.auto()
    MISSING_REQUIRED_PARAMETER = enum.auto()
    UNEXPECTED_BLOCK = enum.auto()
    UNEXPECTED_VALUE = enum.auto()
    BLOCK_INVALID_ID = enum.auto()
    BLOCK_MISSING_ID = enum.auto()
    BLOCK_UNEXPECTED_ID = enum.auto()

    VALUE_WRONG_TYPE = enum.auto()
    VALUE_OUT_OF_RANGE = enum.auto()
    VALUE_PATTERN_MATCH_FAILURE = enum.auto()
    VALUE_INVALID_ENUM = enum.auto()
    # TODO: these are tricky to reimplement with the new system
    VALUE_INCORRECT_VALUE = enum.auto()
    # VALUE_SEQUENCE_MISSING_REQUIRED_ELEMENT = enum.auto()
    # VALUE_SEQUENCE_EXTRA_ELEMENTS = enum.auto()


class ResultVisitor:
    """
    Schema result visitor.

    Subclasses should generally call super() on every method they override, as this is needed for the delegate to work.
    """
    def __init__(self, delegate: ResultVisitor | None = None):
        """
        Creates a ResultVisitor.
        :param delegate: Visitor this visitor should delegate calls to.
        This allows multiple visitors to be chained together.
        """
        self.delegate: ResultVisitor | None = delegate
        """The visitor this visitor should delegate calls to. This allows multiple visitors to be chained together."""

    def visit_block(self, schema: SchemaBlock,
                    block_type: TokenCollection | None, block_id: TokenCollection | None,
                    open_bracket: Token | None, close_bracket: Token | None,
                    errors: list[SchemaError]) -> None:
        """
        Called when visiting a block.
        :param schema: The block's schema.
        :param block_type: The token representing the block's type.
        None if it is the root block of a file, or the block is ill formed.
        :param block_id: The token representing the block's id. None if it does not have one.
        :param open_bracket: Opening bracket of the block. None if it is the root block of a file.
        :param close_bracket: Closing bracket of the block.
        None if it is the root block of a file, or the block is ill formed.
        :param errors: Any schema matching errors raised during validation.
        :return:
        """
        if self.delegate is not None:
            self.delegate.visit_block(schema, block_type, block_id, open_bracket, close_bracket, errors)

    def visit_type(self, schema: SchemaType | None, tokens: TokenCollection,
                   start: int, length: int, errors: list[SchemaError]) -> None:
        """
        Called when visiting the individual components of a value.
        :param schema: Schema of the component.
        :param tokens: The full tokens of the value.
        :param start: Start index, in characters, in ``tokens``.
        :param length: Length in characters.
        :param errors: Any schema matching errors raised during validation.
        :return:
        """
        if self.delegate is not None:
            self.delegate.visit_type(schema, tokens, start, length, errors)

    def visit_pair(self, schema: SchemaType | None, key: TokenCollection, equals: Token, value: TokenCollection,
                   errors: list[SchemaError]) -> None:
        """
        Called when visiting a key-value pair.
        :param schema: Schema of the value.
        :param key: Tokens that make up the key. Surrounding whitespace is trimmed.
        :param equals: Token of the equals sign separating the key and value.
        :param value: Tokens that make up the value. Surrounding whitespace is trimmed.
        :param errors: Any schema matching errors raised during validation.
        :return:
        """
        if self.delegate is not None:
            self.delegate.visit_pair(schema, key, equals, value, errors)

    def visit_value(self, schema: SchemaType | None, value: TokenCollection, errors: list[SchemaError]):
        """
        Called when visiting a non-key-value value.
        :param schema: Schema of the value.
        :param value: Tokens that make up the value. Surrounding whitespace is trimmed.
        :param errors: Any schema matching errors raised during validation.
        :return:
        """
        if self.delegate is not None:
            self.delegate.visit_value(schema, value, errors)


@dataclass
class TypeResult:
    """Result of a schema test on an individual value component."""
    start: int
    """Start index in the full string of the value's tokens."""
    length: int
    """Length in characters of the matched string."""
    schema: SchemaType | None
    """Schema of the value."""
    errors: list[SchemaError] = field(default_factory=list)
    """Schema matching errors."""
    children: list[TypeResult] = field(default_factory=list)
    """Child results. Populated for composite types (lists, sequences)."""


@dataclass
class ValueResult:
    """Result of a schema test for a value."""
    tokens: TokenCollection
    """Tokens of the value."""
    type_result: TypeResult | None
    """Result of the value test. May be none if there is no schema for this parameter."""
    key: TokenCollection | None = None
    """Tokens making up the value's key, if it takes the form of a key-value pair."""
    equals: Token | None = None
    """Token of the ``=`` divider in a key-value pair, if the value is one."""
    errors: list[SchemaError] = field(default_factory=list)
    """Schema matching errors."""


@dataclass
class BlockResult:
    """Result of a schema test for a block."""
    schema: SchemaBlock | None
    """Schema of the block."""
    type: TokenCollection | None
    """Token of the block's type."""
    id: TokenCollection | None
    """Token of the block's id."""
    open_bracket: Token | None
    """Token of the block's opening bracket."""
    close_bracket: Token | None
    """Token of the block's closing bracket."""
    errors: list[SchemaError]
    """Schema matching errors."""
    values: list[ValueResult]
    """Schema test results of the block's values."""
    blocks: list[BlockResult]
    """Schema test results of the block's children"""


def visit_type(result: TypeResult, tokens: TokenCollection, visitor: ResultVisitor) -> None:
    """
    Visits a value component result, recursively visiting any child results.
    :param result: The result to visit.
    :param tokens: The tokens of the value, used to resolve the in-file location and string of the component.
    :param visitor: The visiting ResultVisitor.
    :return:
    """
    visitor.visit_type(
        result.schema,
        tokens,
        result.start,
        result.length,
        result.errors
    )
    for child in result.children:
        visit_type(child, tokens, visitor)


def visit_value(result: ValueResult, visitor: ResultVisitor) -> None:
    """
    Visits a value result, recursively visiting its components.
    :param result: The result to visit.
    :param visitor: The visiting ResultVisitor.
    :return:
    """
    schema = result.type_result.schema if result.type_result is not None else None
    if result.key is not None:
        visitor.visit_pair(schema, result.key, result.equals, result.tokens, result.errors)
    else:
        visitor.visit_value(
            schema,
            result.tokens,
            result.errors
        )

    if result.type_result is not None:
        visit_type(result.type_result, result.tokens, visitor)


def visit_block(result: BlockResult, visitor: ResultVisitor) -> None:
    """
    Visits a block, recursively visiting all children and values.
    :param result: The result to visit.
    :param visitor: The visiting ResultVisitor.
    :return:
    """
    visitor.visit_block(
        result.schema,
        result.type,
        result.id,
        result.open_bracket,
        result.close_bracket,
        result.errors
    )

    for value in result.values:
        visit_value(value, visitor)

    for child in result.blocks:
        visit_block(child, visitor)


# noinspection PyUnusedLocal
@singledispatch
def validate_type(type: SchemaType, tokens: TokenCollection,
                  start: int = 0, end: int | None = None, full_match: bool = True) -> TypeResult | None:
    """
    Returns a CheckResult if ``string`` matches the schema ``type``.
    :param type: Schema type.
    :param tokens: The tokens to check.
    :param start: Offset into the tokens to start from. This is necessary as a type may comprise only part of a token.
    :param end: Offset into the tokens to end at.
    :param full_match: If true, the entire string must be valid. Otherwise, it can match a sequence of characters of any
    length starting from the start of the string.
    :return:
    """
    raise TypeError("check_type not implemented for type " + type.__class__.__name__)


@validate_type.register
def _(type: SchemaTypeString, tokens: TokenCollection,
      start: int = 0, end: int | None = None, full_match: bool = True) -> TypeResult | None:
    if end is None:
        end = len(str(tokens))
    if full_match:
        match = re.fullmatch(PATTERN_ANY, str(tokens)[start:end])
    else:
        match = re.match(PATTERN_ANY, str(tokens)[start:end])
    if match is None:
        return None

    errors = []
    if type.pattern != "" and not re.fullmatch(type.pattern, match.group()):
        errors.append(SchemaError.VALUE_PATTERN_MATCH_FAILURE)

    return TypeResult(
        start, match.end(),
        type, errors
    )


@validate_type.register
def _(type: SchemaTypeEnum, tokens: TokenCollection,
      start: int = 0, end: int | None = None, full_match: bool = True) -> TypeResult | None:
    if end is None:
        end = len(str(tokens))
    if full_match:
        match = re.fullmatch(PATTERN_ANY, str(tokens)[start:end])
    else:
        match = re.match(PATTERN_ANY, str(tokens)[start:end])

    if match is None:
        return None

    errors = []
    if match.group() not in type.members:
        errors.append(SchemaError.VALUE_INVALID_ENUM)

    return TypeResult(
        start, end - start,
        type, errors
    )


@validate_type.register
def _(type: SchemaTypeReference, tokens: TokenCollection,
      start: int = 0, end: int | None = None, full_match: bool = True) -> TypeResult | None:
    if end is None:
        end = len(str(tokens))
    if full_match:
        match = re.fullmatch(PATTERN_ANY, str(tokens)[start:end])
    else:
        match = re.match(PATTERN_ANY, str(tokens)[start:end])

    if match is not None:
        return TypeResult(
            start, match.end(),
            type
        )

    return None


@validate_type.register
def _(type: SchemaTypeFloat, tokens: TokenCollection,
      start: int = 0, end: int | None = None, full_match: bool = True) -> TypeResult | None:
    if end is None:
        end = len(str(tokens))
    if full_match:
        match = re.fullmatch(PATTERN_FLOAT, str(tokens)[start:end])
    else:
        match = re.match(PATTERN_FLOAT, str(tokens)[start:end])

    if match is None:
        return None

    value = float(match.group())

    errors = []
    if (type.max is not None and value > type.max
            or type.min is not None and value < type.min):
        errors.append(SchemaError.VALUE_OUT_OF_RANGE)

    return TypeResult(
        start, match.end(),
        type, errors
    )


@validate_type.register
def _(type: SchemaTypeInteger, tokens: TokenCollection,
      start: int = 0, end: int | None = None, full_match: bool = True) -> TypeResult | None:
    if end is None:
        end = len(str(tokens))
    if full_match:
        match = re.fullmatch(PATTERN_INTEGER, str(tokens)[start:end])
    else:
        match = re.match(PATTERN_INTEGER, str(tokens)[start:end])

    if match is None:
        return None

    value = int(match.group())

    errors = []
    if (type.max is not None and value > type.max
            or type.min is not None and value < type.min):
        errors.append(SchemaError.VALUE_OUT_OF_RANGE)

    return TypeResult(
        start, match.end(),
        type, errors
    )


@validate_type.register
def _(type: SchemaTypeBoolean, tokens: TokenCollection,
      start: int = 0, end: int | None = None, full_match: bool = True) -> TypeResult | None:
    if end is None:
        end = len(str(tokens))
    if full_match:
        match = re.fullmatch(PATTERN_BOOLEAN, str(tokens)[start:end])
    else:
        match = re.match(PATTERN_BOOLEAN, str(tokens)[start:end])

    if match is not None:
        return TypeResult(start, match.end(), type)

    return None

# TODO: surviving through multiple rewrites, the List and Sequence validators got really messy
#  it's very possible that they can be rewritten a lot better than they are currently


@validate_type.register
def _(type: SchemaTypeList, tokens: TokenCollection,
      start: int = 0, end: int | None = None, full_match: bool = True) -> TypeResult | None:
    if end is None:
        end = len(str(tokens))
    string = str(tokens)[start:end]
    if not string.startswith(type.open):
        return None

    if type.close != "":
        end_index = string.find(type.close)
        if (end_index == -1 or
                (full_match and end_index != end - len(type.close))):
            return None
    else:
        end_index = end

    results: list[TypeResult] = []

    pos: int = len(type.open)
    next_separator = 0
    while next_separator < end_index:
        next_separator = string.find(type.separator, pos)
        if next_separator == -1:
            next_separator = end_index
        element_result = validate_type(type.type, tokens, start + pos, start + next_separator)
        if element_result is None:
            return None

        results.append(element_result)
        pos = next_separator + len(type.separator)

    return TypeResult(
        start, end_index + len(type.close),
        type, children=results
    )


@validate_type.register
def _(type: SchemaTypeSequence, tokens: TokenCollection,
      start: int = 0, end: int | None = None, full_match: bool = True) -> TypeResult | None:
    if end is None:
        end = len(str(tokens))
    length: int = 0
    string: str = str(tokens)[start:end]
    end_index = len(string)
    element_idx: int = 0
    any_found_current_element: bool = False
    results: list[TypeResult] = []

    while element_idx < len(type.elements):
        element = type.elements[element_idx]
        separator: re.Match | None = None
        if type.separator != "":
            separator = re.search(type.separator, string[length:])
            if separator is not None:
                end_index = length + separator.start()
            else:
                end_index = len(string)

        result = validate_type(
            element.type, tokens, start + length, start + end_index,
            full_match=separator is not None
        )
        if result is not None:
            results.append(result)
            if separator is not None:
                length += separator.end()
            else:
                length += result.length

            if type.repeatable:
                any_found_current_element = True
            else:
                any_found_current_element = False
                element_idx += 1
        elif any_found_current_element or element.optional:
            any_found_current_element = False
            element_idx += 1
        else:
            return None

    if full_match and length != end_index:
        return None

    return TypeResult(
        start, length,
        type, children=results
    )


@validate_type.register
def _(type: SchemaTypeConst, tokens: TokenCollection,
      start: int = 0, end: int | None = None, full_match: bool = True) -> TypeResult | None:
    if end is None:
        end = len(str(tokens))

    value = re.escape(str(type.value))

    if full_match:
        match = re.fullmatch(value, str(tokens)[start:end])
    else:
        match = re.match(value, str(tokens)[start:end])

    errors = []
    if match is None:
        errors.append(SchemaError.VALUE_INCORRECT_VALUE)

    return TypeResult(
        start, len(value),
        type, errors
    )


def validate_block(schema: SchemaBlock, block: Block) -> BlockResult:
    """
    Validates a block against the schema, including its body, and recursively validates child blocks.
    :param schema: The schema to validate against.
    :param block: The block to validate.
    :return: Result of validation.
    """
    result = validate_body(schema.body, block)
    result.schema = schema

    if block.type != "":
        node = typing.cast(BlockNode, block.node)
        result.type = node.type

        if block.id != "":
            result.id = node.id

    if schema.id_type is IDType.REQUIRED:
        if block.id == "":
            result.errors.append(SchemaError.BLOCK_MISSING_ID)
        elif len(schema.valid_ids) > 0 and block.id not in schema.valid_ids:
            result.errors.append(SchemaError.BLOCK_INVALID_ID)
    elif schema.id_type is IDType.NONE and block.id != "":
        result.errors.append(SchemaError.BLOCK_UNEXPECTED_ID)

    return result


def validate_body(schema: SchemaBlockBody, block: Block) -> BlockResult:
    """
    Validates the body of a block against the schema, and recursively validates child blocks.
    :param schema: The schema to validate against.
    :param block: The block to validate.
    :return: Result of validation.
    """
    parameters = schema.parameters.copy()
    required_parameters = set(schema.required_parameters)

    for conditional in schema.conditionals:
        if conditional.condition.test(block):
            parameters.update(conditional.body.parameters)
            required_parameters = required_parameters.union(conditional.body.required_parameters)

    values: list[ValueResult] = []
    for value in block.values():
        if value.is_key_value():
            value_schema = parameters.get(value.key().lower())
            if value_schema is not None:
                result = ValueResult(
                    value.node.value(),
                    # FIXME: this is None if it is not the correct type
                    #  None is supposed to indicate no schema, not incorrect type!!
                    validate_type(value_schema.type, value.node.value()),
                    value.node.key(),
                    value.node.equals()
                )
                values.append(result)
            else:
                result = ValueResult(value.node.value(), None, value.node.key(), value.node.equals())
                if not schema.extra_parameters:
                    result.errors.append(SchemaError.UNKNOWN_PARAMETER)
                values.append(result)
        elif len(schema.values) > 0:
            any_match: bool = False
            for value_schema in schema.values:
                result = validate_type(value_schema.type, value.node.value())
                if result is not None:
                    any_match = True
                    values.append(
                        ValueResult(value.node.value(), result)
                    )
                    break
            if not any_match:
                values.append(
                    ValueResult(value.node.value(), None, None, None, [SchemaError.VALUE_WRONG_TYPE])
                )
        else:
            values.append(
                ValueResult(value.node.value(), None, None, None, [SchemaError.UNEXPECTED_VALUE])
            )

    children: list[BlockResult] = []
    for child in block.blocks():
        child_schema = schema.blocks.get(child.type)
        if child_schema is not None:
            result = validate_block(child_schema, child)
            children.append(result)
        else:
            assert isinstance(child.node, BlockNode), "Child block is not a block"
            type = child.node.type
            id = child.node.id
            open_bracket = child.node.open_bracket
            close_bracket = child.node.close_bracket
            children.append(
                BlockResult(
                    None, type, id, open_bracket, close_bracket,
                    [SchemaError.UNEXPECTED_BLOCK], [], []
                )
            )

    return BlockResult(None, None, None, None, None, [], values, children)


def first_matching_schema(path: Path, schemas: Iterable[SchemaFile]) -> SchemaFile | None:
    """
    Returns the first schema found in ``schemas`` that ``path`` matches.
    :param path: The path to match.
    :param schemas: Iterable of schema files to check.
    :return: The first matching schema, or None if none of the schemas match.
    """
    for schema in schemas:
        for pattern in schema.valid_file_names:
            if path.match(pattern):
                return schema
    return None


def validate_file(path: Path, body: Block, schema: SchemaFile | Iterable[SchemaFile]) -> BlockResult | None:
    """
    Validates a file against a schema.
    :param path: The path of the file.
    :param body: The root block of the file.
    :param schema: The schema to validate against, or a list of possible to schemas to validate against.
    Only one schema will be tested, based on the ``path``.
    :return: Result of testing against the schema. None if the file was not valid for any schema.
    """
    if isinstance(schema, SchemaFile):
        any_match: bool = False
        for pattern in schema.valid_file_names:
            if path.match(pattern):
                any_match = True
                break
        if not any_match:
            return None
    else:
        schema = first_matching_schema(path, schema)
        if schema is None:
            return None

    return validate_body(schema.body, body)
