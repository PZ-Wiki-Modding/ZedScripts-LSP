import re
from typing import TYPE_CHECKING

from ..enums.SyntaxErrorType import SyntaxErrorType
from .lexer import (
    Lexer, 
    TokenType, Token, TokenCollection, 
    TextRange, TextPosition, 
    ELEMENTS_DELIMITERS
)
from .ast import Node, Chunk, BlockNode, ValueNode
from ..scripts.block import Block, ScriptBlock, Root
from ..scripts.value import Value

if TYPE_CHECKING:
    from ..environment.document import Document

class SyntaxError:
    def __init__(self, type: SyntaxErrorType, location: TextRange) -> None:
        self.type: SyntaxErrorType = type
        self.location: TextRange = location


class ParseResult:
    def __init__(self, chunk: Chunk) -> None:
        self.chunk: Chunk = chunk
        self.errors: list[SyntaxError] = []


class Parser:
    def __init__(self) -> None:
        self.chunk: Chunk = Chunk()
        """Root of the chunk being parsed."""
        self.block_stack: list[BlockNode] = []
        """Stack of the currently parsing blocks."""

    def add_block(self, block: BlockNode) -> None:
        """
        Adds a block to the top of the stack.
        :return: The block that was added.
        """
        if len(self.block_stack) > 0:
            self.block_stack[-1].children.append(block)
        else:
            self.chunk.children.append(block)
        self.block_stack.append(block)

    def add_value(self, value: ValueNode) -> None:
        """
        Adds a value to the block at the top of the stack, or the root if the stack is empty.
        :param value: The value to push.
        :return:
        """
        if len(self.block_stack) > 0:
            self.block_stack[-1].children.append(value)
        else:
            self.chunk.children.append(value)

    def pop_block(self) -> BlockNode:
        """
        Removes the block at the top of the stack.
        :return: The block that was at the top of the stack.
        """
        assert len(self.block_stack) > 0, "Attempted to pop from empty stack"
        return self.block_stack.pop()


def parse_type_id(tokens: list[Token]) -> tuple[TokenCollection | None, TokenCollection | None]:
    type_token = TokenCollection()
    id_token = TokenCollection()
    hit_whitespace = False
    for unparsed_token in tokens:
        if unparsed_token.type is TokenType.TEXT:
            # all tokens before the first whitespace are the type
            if not hit_whitespace:
                type_token.append(unparsed_token)
                # all tokens between the first and second are the id
            else:
                id_token.append(unparsed_token)
        elif len(type_token) > 0 and unparsed_token.type is TokenType.WHITESPACE:
            if not hit_whitespace:
                hit_whitespace = True
            else:
                # after we hit whitespace for a second time, break
                # FIXME: whitespace -> comment -> whitespace should not break
                break

    if len(type_token) < 1:
        type_token = None
    if len(id_token) < 1:
        id_token = None

    return type_token, id_token


def parse(text: str) -> ParseResult:
    return parse_tokens(Lexer.tokenize(text))


def parse_tokens(tokens: TokenCollection) -> ParseResult:
    parser = Parser()
    unparsed_tokens: list[Token] = []
    result: ParseResult = ParseResult(parser.chunk)
    unassigned_comments: list[Token] = []

    for token in tokens:
        match token.type:
            case TokenType.ELEMENT_DELIMITER:
                match token.text:
                    case "}":
                        if len(parser.block_stack) == 0:
                            result.errors.append(
                                SyntaxError(SyntaxErrorType.TOO_MANY_CLOSING_BRACKETS,
                                            TextRange(token.pos, token.end))
                            )
                            break
                        if len(unparsed_tokens) > 1:
                            # necessary when when writing between two block end }
                            # should be -1 when after a key-value def
                            start = 1
                            end = -2 if len(unparsed_tokens) > 2 else -1
                            result.errors.append(
                                SyntaxError(SyntaxErrorType.UNPARSED_TOKENS,
                                            TextRange(unparsed_tokens[start].pos, unparsed_tokens[end].end))
                            )
                        top_block = parser.pop_block()
                        top_block.close_bracket = token
                    case "{":
                        type_token, id_token = parse_type_id(unparsed_tokens)

                        if type_token is None:
                            result.errors.append(
                                SyntaxError(SyntaxErrorType.BLOCK_MISSING_TYPE,
                                            TextRange(token.pos, token.end))
                            )

                        parser.add_block(
                            BlockNode(
                                type_token, id_token, token, None,
                                comments=unassigned_comments
                            )
                        )
                    case ",":
                        value = ValueNode(
                            TokenCollection(unparsed_tokens),
                            token, # comma token
                            comments=unassigned_comments
                        )
                        parser.add_value(value)
                    case _:
                        raise RuntimeError("Unknown punctuator " + token.text)
                unparsed_tokens = []
                unassigned_comments = []
            case TokenType.COMMENT:
                unassigned_comments.append(token)
            case _:
                unparsed_tokens.append(token)

    if len(parser.block_stack) > 0:
        result.errors.append(
            SyntaxError(SyntaxErrorType.BLOCK_NOT_CLOSED,
                        TextRange(parser.block_stack[0].open_bracket.pos, tokens[-1].end))
        )

    return result


def ast_to_comment(node: Node, start: TextPosition) -> str:
    """
    Parses comment tokens from a node into a single string.
    :param node: The node to parse comments from.
    :param start: The start position of the actual object represented by the node.
    :return: The comments merged into a string.
    """
    comment: str = ""

    # we loop backwards to easily ignore comment tokens separated by a non-comment line
    for token in reversed(node.comments):
        if token.end.line < start.line - 1:
            continue

        comment = str(token)[2:-2] + comment

        if token.pos < start:
            start = token.pos

    # remove leading whitespace from each line
    comment = re.sub(r'\n\s+', '\n', comment)
    # remove leading/trailing newlines
    comment = re.sub(r'^\n+', '', comment)
    comment = re.sub(r'\n+$', '', comment)

    return comment


def ast_to_value(node: ValueNode, parent: Block) -> Value:
    tokens = node.tokens.strip()
    if len(tokens) > 0:
        comment = ast_to_comment(node, tokens[0].pos)
    else:
        comment = ""

    value = Value(
        str(node.tokens).strip(),
        node,
        parent,
        comment
    )

    return value

def ast_to_block(document: 'Document', node: BlockNode, parent: Block) -> ScriptBlock:
    if node.type is None:
        type = ""
    else:
        type = str(node.type)
    
    if node.id is None:
        id = None
    else:
        id = str(node.id)

    comment = ast_to_comment(node, node.open_bracket.pos)
    block = ScriptBlock(document, type, id, node, parent, comment)
    ast_to_any(document, block)

    return block


def ast_to_any(document, parent: ScriptBlock | Root):
    if parent.node is None:
        raise RuntimeError("Parent block has no associated AST node.")
    for child in parent.node.children:
        if isinstance(child, ValueNode):
            parent.values.append(ast_to_value(child, parent))
        elif isinstance(child, BlockNode):
            parent.children.append(ast_to_block(document, child, parent))


def chunk_to_root(document: 'Document', chunk: Chunk, rootType: str) -> Root:
    root = Root(document, rootType, chunk, "")
    ast_to_any(document, root)
    return root
