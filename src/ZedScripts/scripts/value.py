from typing import TYPE_CHECKING, Any

from . import Element
from ..enums.Diagnostic import DiagnosticType
from ..structure.ast import ValueNode
from ..structure.lexer import TextRange
from ..providers.semantic_tokens import SemanticTokenType, SemanticTokenModifiers

if TYPE_CHECKING:
    from ..scripts import DeprecatedInfo
    from ..scripts.dataset import Dataset
    from ..scripts.blocks import Block


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

    def __str__(self) -> str:
        return self.string


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

        # verify whenever the parameter is deprecated
        deprecated_data = param_data.get('deprecated', None)
        if deprecated_data is not None:
            depr_type, param = _get_deprecated_info(deprecated_data)
            self.parent.add_diagnostic(
                type=depr_type,
                location=key_node.to_range(),
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

        

        return True
