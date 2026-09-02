import enum
import re

from .blocks import Block, Value, TextPosition
from .lexer import Lexer, TokenType, Token, TokenCollection, TextRange
from .ast import Node, Chunk, BlockNode, ValueNode


class SyntaxErrorType(enum.Enum):
    TOO_MANY_CLOSING_BRACKETS = enum.auto()
    BLOCK_MISSING_TYPE = enum.auto()
    BLOCK_NOT_CLOSED = enum.auto()


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
            case TokenType.PUNCTUATOR:
                match token.text:
                    case "}":
                        if len(parser.block_stack) == 0:
                            result.errors.append(
                                SyntaxError(SyntaxErrorType.TOO_MANY_CLOSING_BRACKETS,
                                            TextRange(token.pos, token.end))
                            )
                            break
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


def ast_to_value(node: ValueNode) -> Value:
    value = Value(
        str(node.tokens).strip()
    )
    value.node = node
    value.comment = ast_to_comment(node, node.tokens.strip()[0].pos)
    return value


def ast_to_block(node: BlockNode) -> Block:
    if node.type is None:
        type = ""
    else:
        type = str(node.type)

    block = Block(type)
    block.node = node
    if node.id is not None:
        block.id = str(node.id)

    for child in node.children:
        if isinstance(child, ValueNode):
            block.elements.append(ast_to_value(child))
        elif isinstance(child, BlockNode):
            block.elements.append(ast_to_block(child))

    block.comment = ast_to_comment(node, node.open_bracket.pos)

    return block


def chunk_to_block(chunk: Chunk) -> Block:
    root = Block("")
    root.node = chunk

    for node in chunk.children:
        if isinstance(node, ValueNode):
            root.elements.append(ast_to_value(node))
        elif isinstance(node, BlockNode):
            root.elements.append(ast_to_block(node))

    return root
