from __future__ import annotations

import enum
import string
from typing import Any
from collections import UserList
# from warnings import deprecated


class TextPosition:
    """
    Position in a text file.
    Positions are zero indexed - in most cases you will want to convert to one-index when displaying to the user.
    """

    def __init__(self, line: int, offset: int) -> None:
        self.line: int = line
        self.offset: int = offset

    @staticmethod
    def from_index(text: str, i: int, offset: TextPosition | None = None) -> TextPosition:
        """
        Returns the TextPosition of a character in a string by its index.
        :param text: The string containing the character.
        :param i: Index of the character.
        :param offset: If specified, the result will be offset as though the start was at this position.
        :return: Position of the character relative to the start of the string.
        """
        if offset is None:
            offset = TextPosition(0, 0)
        lines: int = text.count("\n", 0, i)
        if lines == 0:
            return TextPosition(offset.line, offset.offset + i)
        else:
            return TextPosition(offset.line + lines, i - text.rfind("\n", 0, i) - 1)

    def to_index(self, string: str) -> int:
        newline: int = -1
        for _ in range(self.line):
            newline = string.index("\n", newline + 1)
        return newline + self.offset + 1

    def relative_to(self, other: TextPosition) -> TextPosition:
        """
        Returns a new TextPosition that represents the same position as this one, relative to ``other``.
        :param other:
        :return:
        """
        assert self.line > other.line or (self.line == other.line and self.offset >= other.offset)
        line = self.line - other.line
        offset = self.offset
        if line == 0:
            offset -= other.offset
        return TextPosition(line, offset)

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, TextPosition):
            return NotImplemented
        return self.line > other.line or self.line == other.line and self.offset > other.offset

    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, TextPosition):
            return NotImplemented
        return self.line > other.line or self.line == other.line and self.offset >= other.offset

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, TextPosition):
            return NotImplemented
        return not other >= self

    def __le__(self, other: Any) -> bool:
        if not isinstance(other, TextPosition):
            return NotImplemented
        return not other > self

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, TextPosition):
            return False
        return self.line == other.line and self.offset == other.offset

    def __repr__(self) -> str:
        return f"<{str(self.line)}:{str(self.offset)}>"


class TextRange:
    """
    Range of characters in a text file.

    Range positions should be thought of as between characters:
    A range starting at ``0:0`` and ending at ``0:5`` contains the characters ``0:0`` - ``0:4``.
    """

    def __init__(self, start: TextPosition, end: TextPosition) -> None:
        self.start: TextPosition = start
        self.end: TextPosition = end

    def __repr__(self) -> str:
        return f"<{repr(self.start)}-{repr(self.end)}>"


def chars_in_range(text: str, range: TextRange) -> str:
    """
    Returns a substring of ``text`` containing all characters in the range described by ``range``.

    If ``range`` is not contained within ``text``, an empty string is returned.
    In general, this function is only intended to be used with ranges originally generated from ``text``.
    :param text: The text document.
    :param range: The range of characters to extract.
    :return: Substring of ``text`` described by ``range``.
    """
    lines = text.split('\n')
    if range.end.line >= len(lines):
        return ""

    line_delta = range.end.line - range.start.line

    if line_delta == 0:
        return lines[range.start.line][range.start.offset:range.end.offset]

    result: str = lines[range.start.line][range.start.offset:] + "\n"
    if line_delta > 1:
        result += str.join("\n", lines[range.start.line + 1:range.end.line]) + "\n"
    result += lines[range.end.line][:range.end.offset]
    return result


class TokenType(enum.Enum):
    TEXT = enum.auto()
    WHITESPACE = enum.auto()
    NEWLINE = enum.auto()
    ELEMENT_DELIMITER = enum.auto()
    PUNCTUATOR = enum.auto()
    COMMENT = enum.auto()


ELEMENTS_DELIMITERS: set[str] = {"{", "}", ","}
PUNCTUATORS: set[str] = {"=", ":", ";"}



WHITESPACE_NO_NEWLINE = string.whitespace.replace("\n", "")
"""Whitespace characters without a newline"""



class ZedscriptSource:
    def __init__(self, text: str) -> None:
        self.string: str = text
        self.tokens: TokenCollection = TokenCollection()


class Token:
    def __init__(
            self, type: TokenType, pos: TextPosition, end: TextPosition,
            source: ZedscriptSource, text: str
    ) -> None:
        self.type: TokenType = type
        self.pos: TextPosition = pos
        """Start position of the token."""
        self.end: TextPosition = end
        """End position of the token."""
        self.source: ZedscriptSource = source
        self.text = text

    def pos_of(self, i: int) -> TextPosition:
        """
        Returns the TextPosition of the character at index i in the string.
        :param i: Index of the character.
        :return: Position of the character.
        """
        return TextPosition.from_index(self.text, i, self.pos)

    # @deprecated("Use end property instead.")
    def end_pos(self) -> TextPosition:
        """
        Calculates the end position of the token.
        The end position of a token is the same as the start position of the next token.
        :return:
        """
        return self.end

    def __str__(self) -> str:
        return self.text


class TokenCollection(UserList[Token]):
    def at(self, pos: TextPosition) -> Token | None:
        for token in self.data:
            if token.end > pos:
                if token.pos < pos:
                    raise RuntimeError("pos is not contained within the collection")
                return token
        raise RuntimeError("pos is not contained within the collection")

    def pos_of(self, i: int) -> TextPosition:
        """
        Returns the TextPosition of the character at index ``i`` in the total string of the collection.
        :param i: Character index.
        :return: Position of the character.
        """
        # FIXME: this is a naive implementation, as it assumes there are no gaps between tokens
        #  it is valid for a gap to exist when comments are involved
        total_length: int = 0

        if len(str(self)) == i:
            return self.data[-1].end

        token: Token | None = None
        for token in self.data:
            token_length = len(str(token))
            if total_length + token_length > i:
                break
            total_length += token_length
        assert token is not None

        return token.pos_of(i - total_length)

    def to_range(self) -> TextRange:
        if not self.data:
            return TextRange(TextPosition(0, 0), TextPosition(0, 0))
        return TextRange(self.data[0].pos, self.data[-1].end)

    def strip(self) -> TokenCollection:
        # early return
        end = len(self.data)
        if end == 0:
            return TokenCollection(self.data)

        start: int = 0
        while start < len(self.data):
            if self.data[start].type is not TokenType.WHITESPACE:
                break
            start += 1

        while end >= start:
            if self.data[end - 1].type is not TokenType.WHITESPACE:
                break
            end -= 1

        return TokenCollection(self.data[start:end])

    def __str__(self) -> str:
        return str.join("", [token.text for token in self.data])


# TODO: this class is kinda redundant after all
class TokenBuilder:
    def __init__(self, pos: TextPosition, type: TokenType, source: ZedscriptSource) -> None:
        self.type: TokenType = type
        self.pos: TextPosition = pos
        self.text: str = ""
        self.source: ZedscriptSource = source

    def add(self, char: str) -> None:
        self.text += char

    def build(self, end: TextPosition) -> Token:
        return Token(self.type, self.pos, end, self.source, self.text)


class Lexer:
    def __init__(self, text: str) -> None:
        self.text: str = text
        self.source = ZedscriptSource(text)
        self.pos: int = -1
        self.line: int = 0
        self.offset: int = 0

    def has_next(self) -> bool:
        return self.pos + 1 < len(self.text)

    def next(self) -> str:
        assert self.has_next()
        self.pos += 1
        char: str = self.text[self.pos]
        if char == "\n":
            self.offset = 0
            self.line += 1
        else:
            self.offset += 1
        return char

    def peek(self, num_characters: int = 1) -> str:
        assert self.pos + num_characters < len(self.text)
        return self.text[self.pos + num_characters]

    def start_token(self, type: TokenType) -> TokenBuilder:
        return TokenBuilder(TextPosition(self.line, self.offset), type, self.source)

    def tokenize_comment(self) -> None:
        assert self.check_comment()

        token = self.start_token(TokenType.COMMENT)
        # we already know the first two characters are comment indicators
        token.add(self.next())
        token.add(self.next())

        while self.has_next():
            char = self.next()
            token.add(char)
            if char == "*" and self.peek(1) == "/":
                token.add(self.next())
                break

        self.source.tokens.append(
            token.build(
                TextPosition(self.line, self.offset)
            )
        )

    def check_comment(self) -> bool:
        return self.peek() == "/" and self.peek(2) == "*"

    def tokenize_text(self) -> None:
        token = self.start_token(TokenType.TEXT)

        while self.has_next():
            char = self.peek()
            if self.check_comment() or char in ELEMENTS_DELIMITERS or char in string.whitespace:
                break
            token.add(self.next())

        self.source.tokens.append(
            token.build(
                TextPosition(self.line, self.offset)
            )
        )

    def tokenize_whitespace(self) -> None:
        token = self.start_token(TokenType.WHITESPACE)

        while self.has_next():
            char = self.peek()
            if char not in string.whitespace:
                break
            token.add(self.next())

        self.source.tokens.append(
            token.build(
                TextPosition(self.line, self.offset)
            )
        )

    @staticmethod
    def tokenize(raw: str) -> TokenCollection:
        lexer: Lexer = Lexer(raw)
        while lexer.has_next():
            char = lexer.peek()
            if lexer.check_comment():
                lexer.tokenize_comment()
                continue
            elif char in ELEMENTS_DELIMITERS:
                token = lexer.start_token(TokenType.ELEMENT_DELIMITER)
                token.add(lexer.next())
                lexer.source.tokens.append(
                    token.build(
                        TextPosition(lexer.line, lexer.offset)
                    )
                )
                continue
            elif char in string.whitespace:
                lexer.tokenize_whitespace()
                continue
            lexer.tokenize_text()

        return TokenCollection(lexer.source.tokens)


if __name__ == "__main__":
    from pathlib import Path
    workspace = Path(__file__).parent.parent.parent.parent
    file = workspace / "tests" / "scripts" / "food.txt"
    raw = file.read_text()
    tokens = Lexer.tokenize(raw)
    for token in tokens:
        print(str(token.type).ljust(25) + f'"{token}"')
        print(token.pos, token.end)