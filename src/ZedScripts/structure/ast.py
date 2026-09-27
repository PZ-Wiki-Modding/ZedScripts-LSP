from typing import TYPE_CHECKING, Optional

from .lexer import Token, TokenCollection

if TYPE_CHECKING:
    from .lexer import TextPosition

class BlockBody:
    def __init__(self) -> None:
        super().__init__()
        self.children: list[Node] = []
        """Child nodes."""


class Node:
    """Base class for Zedscript AST nodes."""
    def __init__(self, *, comments: Optional[list[Token]] = None) -> None:
        super().__init__()
        if comments is None:
            comments = []
        self.comments: list[Token] = comments
        """
        Comments for the node.
        For blocks, all comments before the opening bracket are included.
        For values, all comments in the range of the value are included.
        A TokenCollection is not used because the tokens might not be contiguous.
        """


class BlockNode(Node, BlockBody):
    """
    Zedscript block.
    """
    def __init__(
            self, type: TokenCollection | None, id: TokenCollection | None,
            open_bracket: Token, close_bracket: Token | None,
            *, comments: Optional[list[Token]] = None
    ) -> None:
        super().__init__(comments=comments)
        self.type: TokenCollection | None = type
        """
        Tokens representing the type of the block.
        This never has any whitespace, but a collection is used because comments can appear anywhere.
        This will never be None in well formed Zedscript. 
        """
        self.id: TokenCollection | None = id
        """
        Tokens representing the id of the block.
        This never has any whitespace, but a collection is used because comments can appear anywhere.
        """
        self.open_bracket: Token = open_bracket
        """
        Opening bracket token. (``{``)
        """
        self.close_bracket: Token | None = close_bracket
        """
        Closing bracket token. (``}``)
        This will never be None in well formed Zedscript.
        """

    @property
    def tokens(self) -> TokenCollection:
        result = TokenCollection()
        if self.type is not None:
            result.extend(self.type)
        if self.id is not None:
            result.extend(self.id)
        result.append(self.open_bracket)
        if self.close_bracket is not None:
            result.append(self.close_bracket)
        return result

    def well_formed(self) -> bool:
        return self.type is not None and self.close_bracket is not None

    def contains_position(self, text_position: 'TextPosition') -> bool:
        return self.tokens.to_range() == text_position


class ValueNode(Node):
    """
    Zedscript value.
    """
    def __init__(self, tokens: TokenCollection, comma: Token, *, comments: Optional[list[Token]] = None) -> None:
        super().__init__(comments=comments)
        self.tokens: TokenCollection = tokens
        """Tokens comprising the value."""
        self.comma: Token = comma
        """
        Comma token following the value.
        """

    def is_key_value(self) -> bool:
        return "=" in str(self.tokens)

    def value(self) -> TokenCollection:
        if not self.is_key_value():
            return self.tokens.strip()
        value = TokenCollection()

        # for token in reversed(self.tokens):
        found_equal = False
        for token in self.tokens:
            if not found_equal:
                if token.text == "=":
                    found_equal = True
                continue
            # if token.text == "=":
            #     found_equal = True
            #     break
            value.append(token)

        # since we looped backwards, they've been inserted backwards
        # value.reverse()
        return value.strip()

    def key(self) -> TokenCollection:
        assert self.is_key_value()
        key = TokenCollection()

        for token in self.tokens:
            if token.text == "=":
                break
            key.append(token)

        return key.strip()

    def equals(self) -> Token:
        assert self.is_key_value()
        for token in self.tokens:
            if token.text == "=":
                return token
        raise RuntimeError("Couldn't find equals token")

    def contains_position(self, text_position: 'TextPosition') -> bool:
        return self.tokens.to_range() == text_position


class Chunk(BlockBody):
    """
    Root of a Zedscript chunk.
    A chunk is essentially a block body, but we use a separate class to avoid ambiguity.
    """
