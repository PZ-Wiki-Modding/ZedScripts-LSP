from pathlib import Path
from collections.abc import Callable
import json
import logging
from typing import TypeVar, Any

from . import SchemaFile, SchemaBlockBody, SchemaBlock, SchemaParameter, SchemaValue, \
    SchemaConditional, IDType, SchemaType, SchemaCondition, SchemaOperand, SchemaComparator
from .conditions import SchemaOperandParameter, SchemaOperandConst
from .types import SchemaTypeString, SchemaTypeFloat, SchemaTypeInteger, SchemaTypeEnum, \
    SchemaTypeList, SchemaTypeSequence, SchemaTypeReference, ShortReferenceType, SchemaTypeConst

# FIXME: this isn't robust at all lol, the slightest error in the schema crashes

T = TypeVar('T')
ParserT = Callable[[Path, dict[str, Any]], T]

parsers: dict[type[T], ParserT[T]] = {}


def parser[T](cls: type[T]) -> Callable[[ParserT[T]], ParserT[T]]:
    """
    Decorator that registers the function as the parser for that type.
    """
    def decorator(f: ParserT[T]) -> ParserT[T]:
        parsers[cls] = f
        return f
    return decorator


def parse[T](cls: type[T], path: Path, raw: dict[str, Any]) -> T:
    if raw.get("$ref"):
        path = path.parent / Path(raw["$ref"])
        assert path.exists() and path.is_file()
        with path.open("r") as file:
            raw = json.load(file)
        return parse(cls, path, raw)

    if cls not in parsers:
        raise RuntimeError("No parser for class " + cls.__name__)

    return parsers[cls](path, raw)


@parser(SchemaType)
def parse_type(path: Path, raw: dict[str, Any]) -> SchemaType:
    basic = raw["basic"]
    match basic:
        case "string":
            return SchemaTypeString(
                pattern=raw.get("pattern", "")
            )
        case "float":
            return SchemaTypeFloat(
                min=raw.get("minValue"),
                max=raw.get("maxValue")
            )
        case "integer":
            return SchemaTypeInteger(
                min=raw.get("minValue"),
                max=raw.get("maxValue")
            )
        case "enum":
            members: dict[str, SchemaTypeEnum.Member] = {}
            for raw_member in raw["members"]:
                member = SchemaTypeEnum.Member(
                        name=raw_member["name"],
                        description=raw_member.get("description", "")
                    )
                members[member.name] = member
            return SchemaTypeEnum(
                members=members,
                repeatable=raw.get("repeatable", False)
            )
        case "list":
            return SchemaTypeList(
                type=parse(SchemaType, path, raw["type"]),
                separator=raw["delimiters"]["separator"],
                open=raw["delimiters"].get("open", ""),
                close=raw["delimiters"].get("close", "")
            )
        case "sequence":
            if __debug__:
                for element in raw["elements"][:len(raw["elements"]) - 1]:
                    if element["type"]["basic"] == "string" and raw.get("separator") is None:
                        logging.warning("Sequence with no separator has non-terminal string element."
                                        " This is impossible to parse.")
            return SchemaTypeSequence(
                elements=[
                    SchemaTypeSequence.Element(
                        type=parse(SchemaType, path, element["type"]),
                        name=element.get("name", ""),
                        description=element.get("description", ""),
                        optional=element.get("optional", False)
                    ) for element in raw["elements"]
                ],
                separator=raw.get("separator", ""),
                ordered=raw.get("ordered", True),
                repeatable=raw.get("repeatable", False)
            )
        case "reference":
            return SchemaTypeReference(
                group=raw["group"],
                short_reference_type=ShortReferenceType.from_json_name(raw.get("shortReferenceType", "none")),
                allow_qualified_references=raw.get("allowQualifiedReference", True)
            )
        case "const":
            return SchemaTypeConst(
                value=raw["value"]
            )
        case "objectReference":
            # TODO
            return SchemaTypeString(pattern="")

    if basic not in SchemaType.type_map:
        raise RuntimeError("No parser for type basic=" + basic)

    return SchemaType.type_map[basic]()


@parser(SchemaParameter)
def parse_parameter(path: Path, raw: dict[str, Any]) -> SchemaParameter:
    if raw.get("type") is not None:
        type = parse(SchemaType, path, raw["type"])
    else:
        # TODO: temporary hack while the schema is unfinished, delete this later!
        type = SchemaTypeString(
            pattern=""
        )

    return SchemaParameter(
        type=type,
        name=raw["name"],
        description=raw.get("description", ""),
        repeatable=raw.get("repeatable", False),
        default=raw.get("default", ""),
        deprecated=raw.get("deprecated", False)
    )


@parser(SchemaValue)
def parse_value(path: Path, raw: dict[str, Any]) -> SchemaValue:
    return SchemaValue(
        type=parse(SchemaType, path, raw["type"]),
        name=raw["name"],
        description=raw.get("description", ""),
        minOccurrences=raw.get("minOccurrences", 0),
        maxOccurrences=raw.get("maxOccurrences", 0),
        deprecated=raw.get("deprecated", False)
    )


@parser(SchemaOperand)
def parse_operand(path: Path, raw: dict[str, Any]) -> SchemaOperand:
    type = raw["type"]
    match type:
        case "parameter":
            return SchemaOperandParameter(
                name=raw["name"]
            )
        case "const":
            return SchemaOperandConst(
                value=raw["value"]
            )

    return SchemaOperand.type_map[type]()


@parser(SchemaCondition)
def parse_condition(path: Path, raw: dict[str, Any]) -> SchemaCondition:
    return SchemaCondition(
        a=parse(SchemaOperand, path, raw["a"]),
        comparator=SchemaComparator.type_map[raw["comparator"]](),
        b=parse(SchemaOperand, path, raw["b"])
    )


@parser(SchemaConditional)
def parse_conditional(path: Path, raw: dict[str, Any]) -> SchemaConditional:
    return SchemaConditional(
        condition=parse(SchemaCondition, path, raw["condition"]),
        body=parse(SchemaBlockBody, path, raw["body"])
    )


@parser(SchemaBlockBody)
def parse_body(path: Path, raw: dict[str, Any]) -> SchemaBlockBody:
    blocks: dict[str, SchemaBlock] = {}
    for raw_block in raw.get("blocks", []):
        block = parse(SchemaBlock, path, raw_block)
        blocks[block.type] = block

    parameters: dict[str, SchemaParameter] = {}
    for raw_parameter in raw.get("parameters", []):
        parameter = parse(SchemaParameter, path, raw_parameter)
        parameters[parameter.name.lower()] = parameter

    return SchemaBlockBody(
        parameters=parameters,
        values=[parse(SchemaValue, path, value) for value in raw.get("values", [])],
        blocks=blocks,
        extra_parameters=raw.get("extraParameters", False),
        required_parameters=raw.get("requiredParameters", []),
        required_blocks=raw.get("requiredBlocks", []),
        conditionals=[parse(SchemaConditional, path, conditional) for conditional in raw.get("conditionals", [])]
    )


@parser(SchemaBlock)
def parse_block(path: Path, raw: dict[str, Any]) -> SchemaBlock:
    raw_id_type = raw["hasID"]
    if raw_id_type is True:
        id_type = IDType.REQUIRED
    elif raw_id_type is False:
        id_type = IDType.NONE
    elif raw_id_type == "optional":
        id_type = IDType.OPTIONAL
    else:
        raise RuntimeError("Invalid hasID in schema")

    return SchemaBlock(
        type=raw["type"],
        description=raw.get("description", ""),
        id_type=id_type,
        reference_group=raw.get("referenceGroup", ""),
        valid_ids=raw.get("validIds", []),
        repeatable=raw.get("repeatable", False),
        deprecated=raw.get("deprecated", False),
        body=parse(SchemaBlockBody, path, raw["body"])
    )


def parse_file(path: Path) -> SchemaFile | None:
    assert path.exists() and path.is_file()
    with path.open("r") as file:
        raw = json.load(file)

    version = raw.get("version")
    if version is None or version != "1.0":
        return None

    return SchemaFile(
        valid_file_names=raw["validFileNames"],
        body=parse(SchemaBlockBody, path, raw["body"])
    )
