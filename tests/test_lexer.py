"""Offline tests of the language server's production lexer and LSP positions."""
import importlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class LexerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The package initializes its cache/logger on import; isolate that state.
        cls.cache = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.cache.cleanup)
        with patch.object(Path, "home", return_value=Path(cls.cache.name)):
            cls.lexer = importlib.import_module("ZedScripts.structure.lexer")

    def test_empty_document(self):
        self.assertEqual(list(self.lexer.Lexer.tokenize("")), [])

    def test_tokens_preserve_source_and_types(self):
        text = "item Apple { Weight = 0.1, }"
        tokens = self.lexer.Lexer.tokenize(text)
        self.assertEqual(str(tokens), text)
        self.assertEqual(
            [(token.text, token.type.name) for token in tokens if token.type.name != "WHITESPACE"],
            [("item", "TEXT"), ("Apple", "TEXT"), ("{", "ELEMENT_DELIMITER"),
             ("Weight", "TEXT"), ("=", "PUNCTUATOR"), ("0", "TEXT"),
             (".", "PUNCTUATOR"), ("1", "TEXT"), (",", "ELEMENT_DELIMITER"),
             ("}", "ELEMENT_DELIMITER")],
        )

    def test_multiline_comment_is_one_token(self):
        tokens = self.lexer.Lexer.tokenize("/* first\nsecond */\nitem")
        comment, whitespace, item = tokens
        self.assertEqual(comment.type, self.lexer.TokenType.COMMENT)
        self.assertEqual(comment.text, "/* first\nsecond */")
        self.assertEqual((comment.pos.line, comment.pos.offset), (0, 0))
        self.assertEqual((comment.end.line, comment.end.offset), (1, 9))
        self.assertEqual(whitespace.text, "\n")
        self.assertEqual((item.pos.line, item.pos.offset), (2, 0))

    def test_position_round_trips_and_lsp_coordinates(self):
        text = "item\n  Apple\n"
        for index in range(len(text) + 1):
            with self.subTest(index=index):
                pos = self.lexer.TextPosition.from_index(text, index)
                self.assertEqual(pos.to_index(text), index)
                lsp = pos.to_lsp()
                self.assertEqual((lsp.line, lsp.character), (pos.line, pos.offset))

    def test_range_extracts_multiline_text(self):
        position = self.lexer.TextPosition
        span = self.lexer.TextRange(position(0, 2), position(2, 1))
        self.assertEqual(self.lexer.chars_in_range("abcd\nef\ngh", span), "cd\nef\ng")

    def test_existing_script_fixtures_round_trip(self):
        for path in sorted((Path(__file__).parent / "scripts").glob("*.txt")):
            with self.subTest(script=path.name):
                text = path.read_text(encoding="utf-8")
                tokens = self.lexer.Lexer.tokenize(text)
                self.assertEqual(str(tokens), text)
                for token in tokens:
                    span = self.lexer.TextRange(token.pos, token.end)
                    self.assertEqual(self.lexer.chars_in_range(text, span), token.text)
