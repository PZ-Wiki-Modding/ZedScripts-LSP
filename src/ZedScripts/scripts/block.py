from typing import TYPE_CHECKING, Any, Iterator

from . import Element
from ..enums.Diagnostic import DiagnosticType
from ..structure.ast import BlockNode, Chunk
from ..structure.lexer import TextRange
from ..providers.semantic_tokens import SemanticTokenType, SemanticTokenModifier

if TYPE_CHECKING:
    from .value import Value
    from .dataset import Dataset
    from ..environment.document import Document

class Block:
    def __init__(self, document: 'Document', type: str):
        self.document: 'Document' = document
        self.type: str = type
        """
        Type of the block.
        All blocks must have an explicit type, except the root block of a file, which is given an empty string.
        If the block was created from AST, the type may be empty for non-root blocks, but this is ill-formed.
        """
        self.children: list['ScriptBlock'] = []
        self.values: list['Value'] = []

    def __repr__(self) -> str:
        return f"Block(type={self.type}, children={len(self.children)}, values={len(self.values)})"

    def __iter__(self) -> Iterator['ScriptBlock']:
        return iter(self.children)

    def validate(self, dataset: 'Dataset') -> bool: ...
    def validate_block(self, dataset: 'Dataset') -> bool: ...
    def validate_children(self, dataset: 'Dataset') -> None: ...

    def get_keys(self) -> list[str]:
        """
        Get all the keys from the block's key-value pairs.

        Returns:
            list[str]: A list of all keys in the block's key-value pairs, converted to lowercase.
        """
        keys = []
        for value in self.values:
            if value.is_key_value():
                keys.append(value.key().lower())
        return keys

    def check_for_duplicates(self, key: str) -> bool:
        """
        Check if the given key has duplicates within the block's key-value pairs.
        A key is considered a duplicate if it appears more than once in the block's key-value pairs.

        Args:
            key (str): The key to check for duplicates.

        Returns:
            bool: True if the key has duplicates, False otherwise.
        """
        keys = self.get_keys()
        duplicate_count = len([k for k in keys if k == key.lower()])
        return duplicate_count > 1 # > 1 bcs there's itself in the list

    def add_diagnostic(self, type: DiagnosticType, location: TextRange, args: dict[str, Any] = {}) -> None:
        self.document.diagnostics.add(type=type, location=location, args=args)

    def add_semantic_token(self, type: SemanticTokenType, location: TextRange, modifiers: list[SemanticTokenModifier] = []) -> None:
        self.document.semantic_tokens.add(type=type, location=location, modifiers=modifiers)




class ScriptBlock(Block, Element["BlockNode"]):
    def __init__(self, document: 'Document',
                 type: str, id: str | None, 
                 node: BlockNode, parent: Block, 
                 comment: str) -> None:
        super().__init__(document=document, type=type)
        self.id: str | None = id
        """
        ID of the block.
        Blocks are not required to have an ID: this is represented by None.
        """

        self.node = node
        self.comment: str = comment

        self.parent = parent

    def __repr__(self) -> str:
        if self.id is None:
            return "<" + self.type + ">"
        else:
            return "<" + self.type + " " + self.id + ">"



## validation

    def validate(self, dataset: 'Dataset') -> bool:
        # validate self
        if not self.validate_block(dataset):
            # don't validate the rest since they are dependent
            # on the data of this block
            return False

        # validate key-values
        for value in self.values:
            value.validate(dataset)

        # validate children
        self.validate_children(dataset)
        
        return True

    def validate_block(self, dataset: 'Dataset') -> bool:
        """
        Validate the block itself, without considering its children or key-values.
        This includes:
        - validating the block type
        - validating its ID

        Args:
            dataset (Dataset): The dataset used for validation.
            diagnostics (DiagnosticCollection): The collection to which any validation diagnostics should be added.

        Returns:
            bool: True if the block is valid, False otherwise.
        """
        type = self.type
        node = self.node
        if node.type is None or type == "":
            return False
        
        self.add_semantic_token(
            SemanticTokenType.KEYWORD,
            node.type.to_range()
        )

        # validate the type of the block
        if not dataset.is_script_block(type):
            self.add_diagnostic(
                DiagnosticType.BLOCK_UNKNOWN_BLOCK,
                node.type.to_range(),
                {"type": type}
            )
            return False

        # validate the ID of the block
        if not self.validate_id(dataset):
            return False

        return True

    def validate_id(self, dataset: 'Dataset') -> bool:
        type = self.type
        node = self.node
        if node.type is None or type == "":
            return False

        # get ID data
        block_data = dataset.get_script_block_data(self.type)
        ID_data = block_data.get('ID')

        # retrieve ID info
        id = self.id
        has_ID = id is not None

        # no ID data means there shouldn't be any ID
        if has_ID:
            node_id = node.id
            assert node_id is not None, "ID node should not be None when ID is present"

            # add semantic token for the ID
            # that the ID is valid or not
            self.add_semantic_token(
                SemanticTokenType.CLASS,
                node_id.to_range(),
                [SemanticTokenModifier.DECLARATION]
            )

            # there shouldn't be an ID
            if ID_data is None:
                self.add_diagnostic(
                    DiagnosticType.BLOCK_UNEXPECTED_ID,
                    node_id.to_range(),
                    {"type": type, "id": id}
                )
                return False

        # it doesn't have ID needs
        if ID_data is None:
            return True

        # check if ID is optional for this block with a specific parent type
        optional_blocks = ID_data.get('optional')
        if optional_blocks is not None:
            parent_type = self.parent.type
            if parent_type.lower() in [block.lower() for block in optional_blocks]:
                return True # it's optional, so we skip any other checks

        # used to check if the parent block requires an ID for this sub-block
        parents_without = ID_data.get('parentsWithout')
        should_have_id_from_parent = True
        if parents_without is not None:
            parent_type = self.parent.type
            if parent_type.lower() in [block.lower() for block in parents_without]:
                should_have_id_from_parent = False

        # there should be an ID but there isn't one
        if not has_ID:
            if should_have_id_from_parent:
                self.add_diagnostic(
                    DiagnosticType.BLOCK_MISSING_ID,
                    node.type.to_range(),
                    {"id": ID_data}
                )
                return False

        # there is an ID, so validate it
        else:
            if not should_have_id_from_parent:
                assert parents_without is not None, "parents_without should not be None when checking for unexpected ID with specific parent"
                self.add_diagnostic(
                    DiagnosticType.BLOCK_HAS_ID_IN_PARENT,
                    node.type.to_range(),
                    {"type": type, "parent_type": self.parent.type, "invalid_blocks": parents_without}
                )
                return False

            # verify that the ID can have spaces
            can_have_spaces = ID_data.get('canHaveSpace', False)
            if not can_have_spaces and " " in id:
                self.add_diagnostic(
                    DiagnosticType.BLOCK_ID_CANNOT_CONTAIN_SPACES,
                    node.type.to_range(),
                    {"type": type, "id": id}
                )
                return False

            # check if the ID is an accepted value
            valid_IDs = ID_data.get('values')
            if valid_IDs is not None:
                if id not in valid_IDs:
                    self.add_diagnostic(
                        DiagnosticType.BLOCK_INVALID_ID,
                        node.type.to_range(),
                        {"type": type, "id": id, "validIDs": valid_IDs}
                    )
                    return False

                # TODO: this needs to be modified to support a wider range of condition for variants
                # for example specific parameters or parents defining variants

                # whenever we need to consider it as its own type based on the provided ID
                if ID_data.get('asType', False):
                    self.type = self.type + " " + id
                    self.id = None # set the ID to None since it is now part of the type

            # forbidden IDs
            forbidden_IDs = ID_data.get('forbidden')
            if forbidden_IDs is not None:
                if id in forbidden_IDs:
                    self.add_diagnostic(
                        DiagnosticType.BLOCK_FORBIDDEN_ID,
                        node.type.to_range(),
                        {"type": type, "id": id, "forbiddenIDs": forbidden_IDs}
                    )
                    return False

            # TODO: implement ID translation diagnostics
            # requires workspace handling setup

        return True


    def validate_children(self, dataset: 'Dataset') -> None:
        # validate all children blocks
        for child in self.children:
            child.validate(dataset)


class Root(Block, Element["Chunk"]):
    def __init__(self, document: 'Document', type: str, node: Chunk, comment: str) -> None:
        super().__init__(document, type)
        self.type = type
        self.node = node
        self.comment = comment

    def validate(self, dataset: 'Dataset') -> bool:
        # validate key-values
        for value in self.values:
            value.validate(dataset)

        # validate children
        self.validate_children(dataset)
        return True
    
    def validate_children(self, dataset: 'Dataset') -> None:
        # validate all children blocks
        for child in self.children:
            child.validate(dataset)
