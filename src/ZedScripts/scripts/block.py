from typing import TYPE_CHECKING, Any, Iterator

from lsprotocol import types

from .. import SCRIPTSDOCS_LINK
from . import Element
from ..enums.Diagnostic import DiagnosticType
from ..structure.ast import BlockNode, Chunk
from ..structure.lexer import TextRange, TextPosition
from ..providers.semantic_tokens import SemanticTokenType, SemanticTokenModifier
from ..providers.hover import make_hover_information, format_tree

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

    def get_tree(self) -> str:
        type = self.type

        parents: list[str] = [type]
        current = self
        while isinstance(current, ScriptBlock) and current.parent is not None:
            parents.insert(0, current.parent.type)
            current = current.parent

        return " → ".join(parents)

    def get_root(self) -> 'Root': 
        """
        Find the root block of the whole block hierarchy.

        Returns:
            Root: The root block of the whole tree.
        """
        return NotImplemented

    def get_description(self, dataset: 'Dataset') -> str:
        return NotImplemented

    def get_scriptsdocs_url(self, tree: list[str]) -> str:
        return SCRIPTSDOCS_LINK + "/".join(tree).replace(" ", "-").lower()

    def get_hover_information(self, dataset: 'Dataset', text_position: TextPosition) -> types.Hover | None:
        # look through the values
        for value in self.values:
            result = value.get_hover_information(dataset, text_position)
            if result:
                return result

        # not found in values, then we search in the children blocks
        for child in self.children:
            result = child.get_hover_information(dataset, text_position)
            if result is not None:
                return result

        return None

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

        self.node: BlockNode = node
        self.comment: str = comment

        self.parent: Block = parent

    def __repr__(self) -> str:
        if self.id is None:
            return "<" + self.type + ">"
        else:
            return "<" + self.type + " " + self.id + ">"


## information

    def get_root(self) -> 'Root':
        current: Block = self
        i = 0
        while isinstance(current, ScriptBlock) and i < 1000:
            current = current.parent
            i += 1
        assert isinstance(current, Root), "reached iteration limit without finding root"
        return current

    def get_description(self, dataset: 'Dataset') -> str:
        if not dataset.is_script_block(self.type):
            return ''
        block_data = dataset.get_script_block_data(self.type)
        return block_data.get('description', '')

    def get_hover_information(self, dataset: 'Dataset', text_position: TextPosition) -> types.Hover | None:
        if dataset.is_script_block(self.type):
            node = self.node
            type_node = node.type
            if type_node is not None and type_node.strip().to_range() == text_position:
                # show a tree hierarchy of the parameter
                tree = format_tree(self.get_tree())
                desc = self.get_description(dataset)

                # show link to ScriptsDocs
                if dataset.is_script_block(self.type):
                    variant_tree = dataset.get_block_tree(self.type)
                    url = self.get_scriptsdocs_url(variant_tree)
                    tree += f"\n[Documentation]({url})"

                # format the whole thing
                if desc == "":
                    txt = tree
                else:
                    txt = f"{tree}\n\n---\n\n{desc}"

                return make_hover_information(
                    txt,
                    range=self.node.type.to_range() if self.node.type is not None else None,
                )
            # TODO: check ID hover info
        return super().get_hover_information(dataset, text_position)


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

    def get_root(self) -> 'Root': 
        return self

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

    # TODO: this only supports one module block rn
    # but can multiple ones be used by the game ?
    def get_module(self) -> 'ScriptBlock | None':
        """
        Retrieves the module block within the current root block, if it exists.
        """
        for child in self:
            if child.type == "module":
                return child
        return None

    def get_imports(self) -> list[str]:
        """
        Retrieves all the imports of the current module block.
        """
        imports: list[str] = ["Base"]

        # find the module block
        module = self.get_module()
        if module is None:
            return imports

        # search for import statements within the module block
        for child in module:
            if child.type != "import":
                continue
            # retrieve all the values
            for value in child.values:
                if not value.is_key_value():
                    imports.append(value.value())
        return imports
