import logging
from typing import TYPE_CHECKING, Any

from lsprotocol import types

from .. import SCRIPTSDOCS_LINK, IS_DEBUG
from ..utils import path_to_uri
from . import Element
from ..enums.Diagnostic import DiagnosticType
from ..structure.ast import ValueNode
from ..structure.lexer import TextPosition, TokenCollection
from ..providers.semantic_tokens import SemanticTokenType, SemanticTokenModifier
from ..providers.hover import make_hover_information, format_tree
from ..scripts import DeprecatedInfo, ScriptBlockParameter, ValueType

if TYPE_CHECKING:
    from .block import Block, ScriptBlock
    from ..structure.lexer import TextRange
    from ..scripts.dataset import Dataset


def _get_deprecated_info(deprecated_data: 'DeprecatedInfo') -> tuple[DiagnosticType, dict[str, Any]]:
    description = deprecated_data.get('description', "")
    replacement = deprecated_data.get('replacedBy')
    version = deprecated_data.get('version')

    # retrieve relevant arguments for the diagnostic
    params: dict[str, Any] = {
        "description": description,
    }
    if replacement is not None:
        params['replacement'] = replacement
    if version is not None:
        params['version'] = version

    # retrieve the relevant diagnostic type
    diagnostic_type: DiagnosticType
    if replacement is not None and version is not None:
        diagnostic_type = DiagnosticType.VALUE_DEPRECATED_REPLACEMENT_VERSION
    elif replacement is not None:
        diagnostic_type = DiagnosticType.VALUE_DEPRECATED_REPLACEMENT
    elif version is not None:
        diagnostic_type = DiagnosticType.VALUE_DEPRECATED_VERSION
    else:
        diagnostic_type = DiagnosticType.VALUE_DEPRECATED

    return diagnostic_type, params


class Value(Element["ValueNode"]):
    def __init__(self, string: str, node: ValueNode, parent: 'Block', comment: str) -> None:
        super().__init__()
        self.string: str = string
        """
        Includes any whitespace preceding the value, including before any preceding comments.
        This sucks, but it's how the game parses them, so potentially needed for 1:1 behaviour.
        """
        self.node: ValueNode = node
        self.parent: 'Block' = parent
        self.comment: str = comment

        self.refs: list['ScriptBlock'] = []

    def __repr__(self) -> str:
        return f"Value(string={self.string}, parent={self.parent}, comment={self.comment})"

    def __str__(self) -> str:
        return self.string

    def is_key_value(self) -> bool:
        return "=" in self.string

    def key(self) -> str:
        """
        Returns the stripped text before the first ``=`` in the value.
        Not all values take the form of key-value pairs.

        Returns:
            str: The key part of the key-value pair, stripped of surrounding whitespace.
        """
        assert self.is_key_value()
        return self.string.split("=", 1)[0].strip()

    def value(self) -> str:
        """
        Returns the stripped text after the first ``=`` in the value.
        Not all values take the form of key-value pairs.

        Returns:
            str: The value part of the key-value pair, stripped of surrounding whitespace. If the value is not a key-value pair, returns the entire string stripped of surrounding whitespace.
        """
        if self.is_key_value():
            return self.string.split("=", 1)[1].strip()
        return self.string.strip()

    def get_values(self, dataset: 'Dataset', value: str, param_data: 'ScriptBlockParameter') -> list[str]:
        value_type = dataset.get_parameter_type(value, param_data)

        # handle array case
        if value_type == ValueType.ARRAY:
            # we'll want to split by the array data

            # retrieve array related data first
            type_data = param_data.get('type')
            assert type_data
            array_data = type_data.get('array')
            assert array_data

            # split by the separator
            separator = array_data['separator']
            return [v.strip() for v in self.value().split(separator)]

        # handle object case
        elif value_type == ValueType.OBJECT:
            # we simply split by the object's pairs separator

            # retrieve object related data first
            type_data = param_data.get('type')
            assert type_data
            object_data = type_data.get('object')
            assert object_data

            pairs_separator = object_data['pairsSeparator']
            return [v.strip() for v in self.value().split(pairs_separator)]

        # else if we have a value, then it's a single value
        elif value != "":
            return [value]

        return []

    def cleanup_references(self) -> None:
        """Remove itself from any list of references in the previous blocks it references."""
        for ref in self.refs:
            if self in ref.references:
                ref.references.remove(self)
        self.refs.clear()

## information

    def get_tree(self) -> str:
        block_tree = self.parent.get_tree()
        return f"{block_tree} # {self.key()}"

    def get_description(self, dataset: 'Dataset') -> str:
        parent_type = self.parent.type
        key = self.key()
        if not dataset.can_block_have_parameter(parent_type, key):
            return ''
        param_data = dataset.get_parameter_data(parent_type, key)
        return param_data.get('description', '') if param_data else ''

    def get_scriptsdocs_url(self, tree: list[str]) -> str | None:
        return self.parent.get_scriptsdocs_url(tree) + f"#scripts-{self.parent.type}-{self.key()}".replace(' ', '-').lower()

    def get_key_value_hover_information(self, dataset: 'Dataset', text_position: TextPosition) -> types.Hover | None:
        node = self.node
        key_node = node.key()
        value_node = node.value()

        # hovering the parameter, we show information about that
        if key_node.to_range() == text_position:
            # show a tree hierarchy of the parameter and description
            tree = format_tree(self.get_tree())
            desc = self.get_description(dataset)

            # show link to ScriptsDocs
            key = self.key()
            parent_type = self.parent.type
            if dataset.is_script_block(parent_type) \
                and dataset.can_block_have_parameter(parent_type, key):
                variant_tree = dataset.get_block_tree(parent_type)
                url = self.get_scriptsdocs_url(variant_tree)
                tree += f"\n[Documentation]({url})"

            # format the whole thing
            if desc == "":
                txt = tree
            else:
                txt = f"{tree}\n\n---\n\n{desc}"

            return make_hover_information(txt, key_node.to_range())

        # hovering the value, we could show information about the value itself
        if value_node.to_range() == text_position:
            # if its expected type is block, we can list referenced blocks
            txt = ""

            if IS_DEBUG:
                txt += "(debug)\n\n"
                txt += f"- Refs: {[str(ref) for ref in self.refs]}"

            return make_hover_information(txt, value_node.to_range())

        
        return None


    def get_hover_information(self, dataset: 'Dataset', text_position: TextPosition) -> types.Hover | None:
        # hover for key-value
        if self.is_key_value():
            return self.get_key_value_hover_information(dataset, text_position)
        # TODO: hover for non key-value
        return None


## actions

    def get_ref_id_range(self) -> 'TextRange':
        return self.node.value().split()[-1].to_range()

    def get_linked_editing_ranges(self, text_position: TextPosition) -> list['TextRange'] | None:
        if len(self.refs) == 0:
            return None
        ranges: list['TextRange'] = []

        # add the range of the value itself
        ranges.append(self.get_ref_id_range())

        # for each refs, gather their linked editing ranges
        document = self.parent.document
        for ref in self.refs:
            # gather the IDs of blocks that are in the same document only
            if ref.document == document:
                ranges.append(ref.get_ref_id_range())
                continue

            # we gather the referenced ranges from Values that are in the same document
            ranges.extend(ref.get_referenced_to_ranges(self.parent.document))

        return ranges


## definition

    def get_definition(self, text_position: TextPosition) -> list[types.LocationLink] | None:
        if len(self.refs) == 0:
            return None

        result: list[types.LocationLink] = []
        for ref in self.refs:
            ref_id_range = ref.get_ref_id_range().to_lsp()

            location = types.LocationLink(
                target_uri=path_to_uri(ref.document.path),
                target_range=ref_id_range,
                target_selection_range=ref_id_range,
            )
            result.append(location)

        return result


## semantic tokens

    def add_value_type_semantic_tokens(self, actual_type: ValueType, param_data: 'ScriptBlockParameter', value_node: 'TokenCollection') -> None:
        match actual_type:
            case ValueType.FLOAT:
                self.parent.add_semantic_token(
                    type=SemanticTokenType.NUMBER,
                    location=value_node.to_range()
                )
            case ValueType.INTEGER:
                self.parent.add_semantic_token(
                    type=SemanticTokenType.NUMBER,
                    location=value_node.to_range()
                )
            case ValueType.BOOLEAN:
                self.parent.add_semantic_token(
                    type=SemanticTokenType.VARIABLE,
                    location=value_node.to_range()
                )
            case ValueType.BLOCK:
                self.parent.add_semantic_token(
                    type=SemanticTokenType.CLASS,
                    location=value_node.to_range(),
                    modifiers=[SemanticTokenModifier.DEFINITION]
                )

        # the rest is either already handled via the texmate 
        # grammar or shouldn't get specific semantic tokens


## diagnostics

    def validate(self, dataset: 'Dataset') -> bool:
        if self.is_key_value():
            return self.validate_key_value(dataset)

        # TODO: implement validation for non-key-value strings
        
        return True

    def validate_key_value(self, dataset: 'Dataset') -> bool:
        parent_type = self.parent.type

        key = self.key()
        value = self.value()

        node = self.node
        key_node = node.key()
        value_node = node.value()

        self.parent.add_semantic_token(
            type=SemanticTokenType.PARAMETER,
            location=key_node.to_range()
        )

        if not dataset.can_block_have_parameter(parent_type, key):
            # add a diagnostic for the invalid parameter
            self.parent.add_diagnostic(
                type=DiagnosticType.VALUE_UNKNOWN_PARAMETER,
                location=key_node.to_range(),
                args={"type": parent_type, "key": key}
            )
            # technically custom parameters are allowed by the game 
            # and used so we could validate the other stuff too
            # but since other validations depend on parameter data
            # there's nothing else to validate for this parameter
            return False

        param_data = dataset.get_parameter_data(parent_type, key)

        # do the type highlight before anything else
        # so we highlight by type even if the value is otherwise invalid
        type_data = param_data.get('type')
        value_type = dataset.get_parameter_type(value, param_data)
        self.add_value_type_semantic_tokens(value_type, param_data, value_node)

        # check if value has a newline, which is usually not normal
        if "\n" in value:
            self.parent.add_diagnostic(
                type=DiagnosticType.VALUE_WITH_NEWLINE,
                location=value_node.strip().to_range(),
                args={"type": parent_type, "key": key, "value": value}
            )
            # no return, bcs technically still valid for the game
            # so this may be normal

        # verify whenever the parameter is deprecated
        deprecated_data = param_data.get('deprecated', None)
        if deprecated_data is not None:
            depr_type, param = _get_deprecated_info(deprecated_data)
            self.parent.add_diagnostic(
                type=depr_type,
                location=key_node.strip().to_range(),
                args=param
            )
            return False

        # check for duplicates
        can_be_duplicate = param_data.get('allowedDuplicate', False)
        if not can_be_duplicate and self.parent.check_for_duplicates(key):
            self.parent.add_diagnostic(
                type=DiagnosticType.VALUE_DUPLICATE,
                location=key_node.to_range(),
                args={"type": parent_type, "key": key}
            )
            return False

        # check if the value is missing
        can_be_empty = param_data.get('canBeEmpty', False)
        if not can_be_empty and value == "":
            self.parent.add_diagnostic(
                type=DiagnosticType.VALUE_MISSING,
                location=node.tokens.strip().to_range(),
                args={"type": parent_type, "key": key}
            )
            return False

        # we retrieve the list of values
        values = self.get_values(dataset, value, param_data)

        # check forbidden values
        # that is values that are not allowed for this parameter
        accepted_values = param_data.get('values', None)
        if accepted_values is not None:
            # forbidden values are the ones not present in the accepted values list
            forbidden_values = [v for v in values if v not in accepted_values]

            # if the list is not empty, then we have forbidden values for this parameter
            if forbidden_values:
                self.parent.add_diagnostic(
                    type=DiagnosticType.VALUE_FORBIDDEN,
                    location=value_node.to_range(),
                    args={"type": parent_type, "key": key, 
                          "forbidden_values": forbidden_values, 
                          "accepted_values": accepted_values}
                )
                return False

        # init key_value_separator
        # if it is equal to "=", we need to ignore the diagnostic of extra = signs
        # possibly marking a wrongly formatted key-value pair
        key_value_separator = None

        # verify the type
        if value_type is not None and type_data is not None:
            # first we verify that the expected type and the actual 
            # type of the value correspond
            expected_type = type_data['main']
            if value_type != expected_type:
                self.parent.add_diagnostic(
                    type=DiagnosticType.VALUE_INVALID_TYPE,
                    location=value_node.strip().to_range(),
                    args={"key": key, "value": value, "expected_type": expected_type, "actual_type": value_type}
                )
                return False

            # verify based on type
            match expected_type:
                # if it's a translation type, then we need to verify it
                case ValueType.TRANSLATION:
                # TODO: needs to implement
                    pass

                # if it's an object, then we verify the object composition
                case ValueType.OBJECT:
                    # retrieve the object data
                    object_data = type_data.get('object')
                    assert object_data is not None

                    # first make sure that each pairs contain the key-value separator
                    key_value_separator = object_data['keyValueSeparator']
                    for v in values:
                        if key_value_separator not in v:
                            self.parent.add_diagnostic(
                                type=DiagnosticType.VALUE_INVALID_OBJECT_FORMAT,
                                location=value_node.to_range(),
                                args={"type": parent_type, "key": key, "key_value_separator": key_value_separator}
                            )
                            return False

                    # then check if the key and values have the right format
                    obj_key_type = object_data['keyType']
                    obj_value_type = object_data['valueType']
                    failed = False
                    for v in values:
                        # we test each key and value for a type
                        obj_key, obj_value = v.split(key_value_separator, 1)
                        key_type_result = dataset.test_for_type(obj_key_type, obj_key)
                        value_type_result = dataset.test_for_type(obj_value_type, obj_value)

                        # if the expected type and actual type doesn't correspond, then something
                        # is wrong and we need to report a diagnostic
                        if key_type_result != obj_key_type:
                            self.parent.add_diagnostic(
                                type=DiagnosticType.VALUE_INVALID_OBJECT_KEY_TYPE,
                                location=value_node.to_range(),
                                args={"obj_key": obj_key, "key": key, 
                                    "expected_type": obj_key_type, 
                                    "actual_type": key_type_result}
                            )
                            failed = True
                        if value_type_result != obj_value_type:
                            self.parent.add_diagnostic(
                                type=DiagnosticType.VALUE_INVALID_OBJECT_VALUE_TYPE,
                                location=value_node.to_range(),
                                args={"obj_value": obj_value, "key": key, 
                                    "expected_type": obj_value_type, 
                                    "actual_type": value_type_result}
                            )
                            failed = True

                        # verify by

                    # if at least one failed, then the entire object is considered invalid
                    if failed:
                        return False

                # if it's a block type, then it needs to reference another block
                case ValueType.BLOCK:
                    passed = self.validate_block_ref(value, param_data, value_node)
                    if not passed:
                        return False

        # diagnostic possibly wrongly formatted key-value pair
        if key_value_separator != "=":
            if "=" in value:
                self.parent.add_diagnostic(
                    type=DiagnosticType.VALUE_WRONGLY_FORMATTED_KEY_VALUE_PAIR,
                    location=node.tokens.strip().to_range(),
                    args={"type": parent_type, "key": key, "value": value}
                )
                return False

        # TODO: need to validate dependent parameters (needs)

        return True

    # TODO: need to implement this function usage
    # def validate_type(self, dataset: Dataset, value: str, expected_type: ValueType, node: TokenCollection, block_type_data: BlockType | None = None) -> bool:
    #     # test for type the value
    #     value_type = dataset.test_for_type(expected_type, value)
    #     if value_type != expected_type:
    #         return False

    #     # if it expects a block reference, then validate that
    #     if (expected_type == ValueType.BLOCK
    #         and block_type_data is not None 
    #         and not self.validate_block_ref(value, block_type_data, node)):
    #         return False

    #     return True

    def block_ref_to_fulltype(self, value: str) -> tuple[str | None, str] | None:
        module = None
        block = None

        parts = value.split(".")
        match len(parts):
            case 2:
                module, block = parts
                return module, block
            case 1:
                block = parts[0]
                return None, block
            case _:
                return None # invalid format

    def validate_block_ref(self, value: str, param_data: ScriptBlockParameter, node: TokenCollection) -> bool:
        type_data = param_data.get('type')
        assert type_data is not None, "Type data must be provided in the parameter data"
        block_type_data = type_data.get('block')
        assert block_type_data is not None, "Block type data must be provided in the type data"

        can_be_empty = block_type_data.get('canBeEmpty', False)

        # retrieve the full type elements
        fulltype = self.block_ref_to_fulltype(value)
        if fulltype is None:
            self.parent.add_diagnostic(
                type=DiagnosticType.VALUE_INVALID_BLOCK_REFERENCE,
                location=node.strip().to_range(),
                args={"value": value}
            )
            return False

        module = fulltype[0]
        block = fulltype[1]

        # check that a module can be provided
        can_full_type = block_type_data.get('fullType', False)
        if not can_full_type and module is not None:
            self.parent.add_diagnostic(
                type=DiagnosticType.VALUE_CANNOT_PROVIDE_MODULE,
                location=node.strip().to_range(),
                args={"value": value, "module": module}
            )
            return False

        # check whenever the block can be empty
        if block == "":
            if can_be_empty:
                return True
            self.parent.add_diagnostic(
                type=DiagnosticType.VALUE_BLOCK_REF_CANNOT_BE_EMPTY,
                location=node.strip().to_range(),
                args={"value": value}
            )
            return False

        # TODO: look for the source block

        root = self.parent.get_root()

        # retrieve imports
        searchable_modules: list[str]
        if module is None:
            searchable_modules = []
        else:
            searchable_modules = root.get_imports()

            # the used module is searched into too
            searchable_modules.append(module)

        # if allowed, auto import the parent module block
        if not block_type_data.get('noAutoImport', False):
            module_block = root.get_module()
            if (module_block is not None
                and module_block.id is not None
                and module_block.id not in searchable_modules):
                searchable_modules.append(module_block.id)

        # search the block reference in the searchable modules
        ref_type = block_type_data['name']
        # FIXME: this is calling a static function as an instance method, not sure that's correct to do that
        # but it had to be done due to circular dependency issues
        self.cleanup_references()
        refs = self.parent.document.workspace.search_for_block_references(root.document.version, searchable_modules, block, ref_type)
        self.refs = refs # cache result since that is used for other providers

        # cache itself inside refs
        for ref in refs:
            ref.references.append(self)

        # diagnostics handling
        refs_len = len(refs)
        if refs_len == 0:
            self.parent.add_diagnostic(
                type=DiagnosticType.VALUE_UNMATCHED_BLOCK_REF,
                location=node.strip().to_range(),
                args={"value": value, "parameter": ref_type, "expected_block": block}
            )
            return False
        if refs_len > 1:
            self.parent.add_diagnostic(
                type=DiagnosticType.VALUE_MULTIPLE_BLOCK_REFS,
                location=node.strip().to_range(),
                args={"value": value, "parameter": ref_type, "expected_block": block}
            )
            return False

        return True
