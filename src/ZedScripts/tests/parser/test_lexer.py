
import argparse

from ZedScripts.structure.lexer import Lexer, TextPosition, TokenType, Token, TokenCollection

def get_example() -> str:
    EXAMPLE_SCRIPT_CONTENT = r"""
module Base {
    item ItemTest {
        param1 = value,
        param2 = val1;val2;val3,
        param3 = key1:val1;key2:val2,

        param4= value,
        param5 =value,
        param6=value,
        param7       =                   fuck you ?,

        weird_param = key1=val1:key2=val2,

        to_new_line = 
        value,

        /* values */
        value1,
        value2,
        value3,
        value4:value5,
    }

    sound SoundTest {
        clip = this/path/to/clip, volume = 0.8,
    }

    model id with spaces {
    
    }

    /* comment, different syntax block under
    hello world *//* comment continued */
    
    this_is_a_weird_block {
    
    }

    item ItemTest2
    {

    }
}
    """.strip()
    return EXAMPLE_SCRIPT_CONTENT

def parse_example_content() -> TokenCollection:
    return Lexer.tokenize(get_example())


def get_theorical_tokens():
    EXPECTED_LEXICAL_TOKENS = TokenCollection(
        [
            Token(TokenType.TEXT, TextPosition(0, 0), TextPosition(0, 6), 'module'),
            Token(TokenType.WHITESPACE, TextPosition(0, 6), TextPosition(0, 7), ' '),
            Token(TokenType.TEXT, TextPosition(0, 7), TextPosition(0, 11), 'Base'),
            Token(TokenType.WHITESPACE, TextPosition(0, 11), TextPosition(0, 12), ' '),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(0, 12), TextPosition(0, 13), '{'),
            Token(TokenType.WHITESPACE, TextPosition(0, 13), TextPosition(1, 4), '\n    '),
            Token(TokenType.TEXT, TextPosition(1, 4), TextPosition(1, 8), 'item'),
            Token(TokenType.WHITESPACE, TextPosition(1, 8), TextPosition(1, 9), ' '),
            Token(TokenType.TEXT, TextPosition(1, 9), TextPosition(1, 17), 'ItemTest'),
            Token(TokenType.WHITESPACE, TextPosition(1, 17), TextPosition(1, 18), ' '),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(1, 18), TextPosition(1, 19), '{'),
            Token(TokenType.WHITESPACE, TextPosition(1, 19), TextPosition(2, 8), '\n        '),
            Token(TokenType.TEXT, TextPosition(2, 8), TextPosition(2, 14), 'param1'),
            Token(TokenType.WHITESPACE, TextPosition(2, 14), TextPosition(2, 15), ' '),
            Token(TokenType.PUNCTUATOR, TextPosition(2, 15), TextPosition(2, 16), '='),
            Token(TokenType.WHITESPACE, TextPosition(2, 16), TextPosition(2, 17), ' '),
            Token(TokenType.TEXT, TextPosition(2, 17), TextPosition(2, 22), 'value'),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(2, 22), TextPosition(2, 23), ','),
            Token(TokenType.WHITESPACE, TextPosition(2, 23), TextPosition(3, 8), '\n        '),
            Token(TokenType.TEXT, TextPosition(3, 8), TextPosition(3, 14), 'param2'),
            Token(TokenType.WHITESPACE, TextPosition(3, 14), TextPosition(3, 15), ' '),
            Token(TokenType.PUNCTUATOR, TextPosition(3, 15), TextPosition(3, 16), '='),
            Token(TokenType.WHITESPACE, TextPosition(3, 16), TextPosition(3, 17), ' '),
            Token(TokenType.TEXT, TextPosition(3, 17), TextPosition(3, 21), 'val1'),
            Token(TokenType.PUNCTUATOR, TextPosition(3, 21), TextPosition(3, 22), ';'),
            Token(TokenType.TEXT, TextPosition(3, 22), TextPosition(3, 26), 'val2'),
            Token(TokenType.PUNCTUATOR, TextPosition(3, 26), TextPosition(3, 27), ';'),
            Token(TokenType.TEXT, TextPosition(3, 27), TextPosition(3, 31), 'val3'),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(3, 31), TextPosition(3, 32), ','),
            Token(TokenType.WHITESPACE, TextPosition(3, 32), TextPosition(4, 8), '\n        '),
            Token(TokenType.TEXT, TextPosition(4, 8), TextPosition(4, 14), 'param3'),
            Token(TokenType.WHITESPACE, TextPosition(4, 14), TextPosition(4, 15), ' '),
            Token(TokenType.PUNCTUATOR, TextPosition(4, 15), TextPosition(4, 16), '='),
            Token(TokenType.WHITESPACE, TextPosition(4, 16), TextPosition(4, 17), ' '),
            Token(TokenType.TEXT, TextPosition(4, 17), TextPosition(4, 21), 'key1'),
            Token(TokenType.PUNCTUATOR, TextPosition(4, 21), TextPosition(4, 22), ':'),
            Token(TokenType.TEXT, TextPosition(4, 22), TextPosition(4, 26), 'val1'),
            Token(TokenType.PUNCTUATOR, TextPosition(4, 26), TextPosition(4, 27), ';'),
            Token(TokenType.TEXT, TextPosition(4, 27), TextPosition(4, 31), 'key2'),
            Token(TokenType.PUNCTUATOR, TextPosition(4, 31), TextPosition(4, 32), ':'),
            Token(TokenType.TEXT, TextPosition(4, 32), TextPosition(4, 36), 'val2'),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(4, 36), TextPosition(4, 37), ','),
            Token(TokenType.WHITESPACE, TextPosition(4, 37), TextPosition(6, 8), '\n\n        '),
            Token(TokenType.TEXT, TextPosition(6, 8), TextPosition(6, 14), 'param4'),
            Token(TokenType.PUNCTUATOR, TextPosition(6, 14), TextPosition(6, 15), '='),
            Token(TokenType.WHITESPACE, TextPosition(6, 15), TextPosition(6, 16), ' '),
            Token(TokenType.TEXT, TextPosition(6, 16), TextPosition(6, 21), 'value'),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(6, 21), TextPosition(6, 22), ','),
            Token(TokenType.WHITESPACE, TextPosition(6, 22), TextPosition(7, 8), '\n        '),
            Token(TokenType.TEXT, TextPosition(7, 8), TextPosition(7, 14), 'param5'),
            Token(TokenType.WHITESPACE, TextPosition(7, 14), TextPosition(7, 15), ' '),
            Token(TokenType.PUNCTUATOR, TextPosition(7, 15), TextPosition(7, 16), '='),
            Token(TokenType.TEXT, TextPosition(7, 16), TextPosition(7, 21), 'value'),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(7, 21), TextPosition(7, 22), ','),
            Token(TokenType.WHITESPACE, TextPosition(7, 22), TextPosition(8, 8), '\n        '),
            Token(TokenType.TEXT, TextPosition(8, 8), TextPosition(8, 14), 'param6'),
            Token(TokenType.PUNCTUATOR, TextPosition(8, 14), TextPosition(8, 15), '='),
            Token(TokenType.TEXT, TextPosition(8, 15), TextPosition(8, 20), 'value'),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(8, 20), TextPosition(8, 21), ','),
            Token(TokenType.WHITESPACE, TextPosition(8, 21), TextPosition(9, 8), '\n        '),
            Token(TokenType.TEXT, TextPosition(9, 8), TextPosition(9, 14), 'param7'),
            Token(TokenType.WHITESPACE, TextPosition(9, 14), TextPosition(9, 21), '       '),
            Token(TokenType.PUNCTUATOR, TextPosition(9, 21), TextPosition(9, 22), '='),
            Token(TokenType.WHITESPACE, TextPosition(9, 22), TextPosition(9, 41), '                   '),
            Token(TokenType.TEXT, TextPosition(9, 41), TextPosition(9, 45), 'fuck'),
            Token(TokenType.WHITESPACE, TextPosition(9, 45), TextPosition(9, 46), ' '),
            Token(TokenType.TEXT, TextPosition(9, 46), TextPosition(9, 49), 'you'),
            Token(TokenType.WHITESPACE, TextPosition(9, 49), TextPosition(9, 50), ' '),
            Token(TokenType.TEXT, TextPosition(9, 50), TextPosition(9, 51), '?'),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(9, 51), TextPosition(9, 52), ','),
            Token(TokenType.WHITESPACE, TextPosition(9, 52), TextPosition(11, 8), '\n\n        '),
            Token(TokenType.TEXT, TextPosition(11, 8), TextPosition(11, 19), 'weird_param'),
            Token(TokenType.WHITESPACE, TextPosition(11, 19), TextPosition(11, 20), ' '),
            Token(TokenType.PUNCTUATOR, TextPosition(11, 20), TextPosition(11, 21), '='),
            Token(TokenType.WHITESPACE, TextPosition(11, 21), TextPosition(11, 22), ' '),
            Token(TokenType.TEXT, TextPosition(11, 22), TextPosition(11, 26), 'key1'),
            Token(TokenType.PUNCTUATOR, TextPosition(11, 26), TextPosition(11, 27), '='),
            Token(TokenType.TEXT, TextPosition(11, 27), TextPosition(11, 31), 'val1'),
            Token(TokenType.PUNCTUATOR, TextPosition(11, 31), TextPosition(11, 32), ':'),
            Token(TokenType.TEXT, TextPosition(11, 32), TextPosition(11, 36), 'key2'),
            Token(TokenType.PUNCTUATOR, TextPosition(11, 36), TextPosition(11, 37), '='),
            Token(TokenType.TEXT, TextPosition(11, 37), TextPosition(11, 41), 'val2'),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(11, 41), TextPosition(11, 42), ','),
            Token(TokenType.WHITESPACE, TextPosition(11, 42), TextPosition(13, 8), '\n\n        '),
            Token(TokenType.TEXT, TextPosition(13, 8), TextPosition(13, 19), 'to_new_line'),
            Token(TokenType.WHITESPACE, TextPosition(13, 19), TextPosition(13, 20), ' '),
            Token(TokenType.PUNCTUATOR, TextPosition(13, 20), TextPosition(13, 21), '='),
            Token(TokenType.WHITESPACE, TextPosition(13, 21), TextPosition(14, 8), ' \n        '),
            Token(TokenType.TEXT, TextPosition(14, 8), TextPosition(14, 13), 'value'),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(14, 13), TextPosition(14, 14), ','),
            Token(TokenType.WHITESPACE, TextPosition(14, 14), TextPosition(16, 8), '\n\n        '),
            Token(TokenType.COMMENT, TextPosition(16, 8), TextPosition(16, 20), '/* values */'),
            Token(TokenType.WHITESPACE, TextPosition(16, 20), TextPosition(17, 8), '\n        '),
            Token(TokenType.TEXT, TextPosition(17, 8), TextPosition(17, 14), 'value1'),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(17, 14), TextPosition(17, 15), ','),
            Token(TokenType.WHITESPACE, TextPosition(17, 15), TextPosition(18, 8), '\n        '),
            Token(TokenType.TEXT, TextPosition(18, 8), TextPosition(18, 14), 'value2'),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(18, 14), TextPosition(18, 15), ','),
            Token(TokenType.WHITESPACE, TextPosition(18, 15), TextPosition(19, 8), '\n        '),
            Token(TokenType.TEXT, TextPosition(19, 8), TextPosition(19, 14), 'value3'),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(19, 14), TextPosition(19, 15), ','),
            Token(TokenType.WHITESPACE, TextPosition(19, 15), TextPosition(20, 8), '\n        '),
            Token(TokenType.TEXT, TextPosition(20, 8), TextPosition(20, 14), 'value4'),
            Token(TokenType.PUNCTUATOR, TextPosition(20, 14), TextPosition(20, 15), ':'),
            Token(TokenType.TEXT, TextPosition(20, 15), TextPosition(20, 21), 'value5'),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(20, 21), TextPosition(20, 22), ','),
            Token(TokenType.WHITESPACE, TextPosition(20, 22), TextPosition(21, 4), '\n    '),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(21, 4), TextPosition(21, 5), '}'),
            Token(TokenType.WHITESPACE, TextPosition(21, 5), TextPosition(23, 4), '\n\n    '),
            Token(TokenType.TEXT, TextPosition(23, 4), TextPosition(23, 9), 'sound'),
            Token(TokenType.WHITESPACE, TextPosition(23, 9), TextPosition(23, 10), ' '),
            Token(TokenType.TEXT, TextPosition(23, 10), TextPosition(23, 19), 'SoundTest'),
            Token(TokenType.WHITESPACE, TextPosition(23, 19), TextPosition(23, 20), ' '),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(23, 20), TextPosition(23, 21), '{'),
            Token(TokenType.WHITESPACE, TextPosition(23, 21), TextPosition(24, 8), '\n        '),
            Token(TokenType.TEXT, TextPosition(24, 8), TextPosition(24, 12), 'clip'),
            Token(TokenType.WHITESPACE, TextPosition(24, 12), TextPosition(24, 13), ' '),
            Token(TokenType.PUNCTUATOR, TextPosition(24, 13), TextPosition(24, 14), '='),
            Token(TokenType.WHITESPACE, TextPosition(24, 14), TextPosition(24, 15), ' '),
            Token(TokenType.TEXT, TextPosition(24, 15), TextPosition(24, 32), 'this/path/to/clip'),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(24, 32), TextPosition(24, 33), ','),
            Token(TokenType.WHITESPACE, TextPosition(24, 33), TextPosition(24, 34), ' '),
            Token(TokenType.TEXT, TextPosition(24, 34), TextPosition(24, 40), 'volume'),
            Token(TokenType.WHITESPACE, TextPosition(24, 40), TextPosition(24, 41), ' '),
            Token(TokenType.PUNCTUATOR, TextPosition(24, 41), TextPosition(24, 42), '='),
            Token(TokenType.WHITESPACE, TextPosition(24, 42), TextPosition(24, 43), ' '),
            Token(TokenType.TEXT, TextPosition(24, 43), TextPosition(24, 44), '0'),
            Token(TokenType.PUNCTUATOR, TextPosition(24, 44), TextPosition(24, 45), '.'),
            Token(TokenType.TEXT, TextPosition(24, 45), TextPosition(24, 46), '8'),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(24, 46), TextPosition(24, 47), ','),
            Token(TokenType.WHITESPACE, TextPosition(24, 47), TextPosition(25, 4), '\n    '),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(25, 4), TextPosition(25, 5), '}'),
            Token(TokenType.WHITESPACE, TextPosition(25, 5), TextPosition(27, 4), '\n\n    '),
            Token(TokenType.TEXT, TextPosition(27, 4), TextPosition(27, 9), 'model'),
            Token(TokenType.WHITESPACE, TextPosition(27, 9), TextPosition(27, 10), ' '),
            Token(TokenType.TEXT, TextPosition(27, 10), TextPosition(27, 12), 'id'),
            Token(TokenType.WHITESPACE, TextPosition(27, 12), TextPosition(27, 13), ' '),
            Token(TokenType.TEXT, TextPosition(27, 13), TextPosition(27, 17), 'with'),
            Token(TokenType.WHITESPACE, TextPosition(27, 17), TextPosition(27, 18), ' '),
            Token(TokenType.TEXT, TextPosition(27, 18), TextPosition(27, 24), 'spaces'),
            Token(TokenType.WHITESPACE, TextPosition(27, 24), TextPosition(27, 25), ' '),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(27, 25), TextPosition(27, 26), '{'),
            Token(TokenType.WHITESPACE, TextPosition(27, 26), TextPosition(29, 4), '\n    \n    '),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(29, 4), TextPosition(29, 5), '}'),
            Token(TokenType.WHITESPACE, TextPosition(29, 5), TextPosition(31, 4), '\n\n    '),
            Token(TokenType.COMMENT, TextPosition(31, 4), TextPosition(32, 18), '/* comment, different syntax block under\n    hello world */'),
            Token(TokenType.COMMENT, TextPosition(32, 18), TextPosition(32, 41), '/* comment continued */'),
            Token(TokenType.WHITESPACE, TextPosition(32, 41), TextPosition(34, 4), '\n    \n    '),
            Token(TokenType.TEXT, TextPosition(34, 4), TextPosition(34, 25), 'this_is_a_weird_block'),
            Token(TokenType.WHITESPACE, TextPosition(34, 25), TextPosition(34, 26), ' '),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(34, 26), TextPosition(34, 27), '{'),
            Token(TokenType.WHITESPACE, TextPosition(34, 27), TextPosition(36, 4), '\n    \n    '),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(36, 4), TextPosition(36, 5), '}'),
            Token(TokenType.WHITESPACE, TextPosition(36, 5), TextPosition(38, 4), '\n\n    '),
            Token(TokenType.TEXT, TextPosition(38, 4), TextPosition(38, 8), 'item'),
            Token(TokenType.WHITESPACE, TextPosition(38, 8), TextPosition(38, 9), ' '),
            Token(TokenType.TEXT, TextPosition(38, 9), TextPosition(38, 18), 'ItemTest2'),
            Token(TokenType.WHITESPACE, TextPosition(38, 18), TextPosition(39, 4), '\n    '),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(39, 4), TextPosition(39, 5), '{'),
            Token(TokenType.WHITESPACE, TextPosition(39, 5), TextPosition(41, 4), '\n\n    '),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(41, 4), TextPosition(41, 5), '}'),
            Token(TokenType.WHITESPACE, TextPosition(41, 5), TextPosition(42, 0), '\n'),
            Token(TokenType.ELEMENT_DELIMITER, TextPosition(42, 0), TextPosition(42, 1), '}'),
        ]
    )
    return EXPECTED_LEXICAL_TOKENS




def generate_theorical_tokens(*args):
    """
    Assuming the tokens currently being parsed are already the right ones, generate the comparison list of theorical tokens
    we are supposed to compare against.
    """
    lexical_tokens = parse_example_content()
    for token in lexical_tokens:
        print(f"Token({token.type}, TextPosition({token.pos.line}, {token.pos.offset}), TextPosition({token.end.line}, {token.end.offset}), {token.text!r}),")

def test_lexer(*args):
    """Test the lexer by comparing its output against the theorical tokens."""
    lexical_tokens = parse_example_content()
    theorical_tokens = get_theorical_tokens()

    for token, theorical_token in zip(lexical_tokens, theorical_tokens):
        print(repr(theorical_token).ljust(80), repr(token).ljust(80))
        assert token == theorical_token, f"Theorical token: {theorical_token!r}, Actual token: {token!r}"


def test_pygments(args: argparse.Namespace | None = None):
    try:
        from ZedScripts.structure.pygments_lexer import highlight_zedscripts
        from pygments import highlight
        from pygments.formatters import TerminalFormatter, Terminal256Formatter

    # if pygments is not installed, then don't run this test
    except ImportError:
        print("Pygments is not installed, skipping the test.")
        return

    xterm = True if args is not None and args.xterm else False

    print(
        highlight_zedscripts(
            get_example(), 
            Terminal256Formatter() if xterm else TerminalFormatter()))


def test_pygments_comments(*args):
    try:
        from ZedScripts.structure.pygments_lexer import ZedScriptsLexer
        from pygments.token import Comment, Error, Name
    except ImportError:
        print("Pygments is not installed, skipping the test.")
        return

    tokens = list(ZedScriptsLexer().get_tokens(get_example()))
    comment_text = "".join(value for token_type, value in tokens if token_type in Comment.Multiline)
    assert "/* values */" in comment_text
    assert "/* comment, different syntax block under\n    hello world */" in comment_text
    assert "/* comment continued */" in comment_text
    assert not [value for token_type, value in tokens if token_type in Error]
    assert (Name.Class, "ItemTest") in tokens




def main():
    import argparse

    main_parser = argparse.ArgumentParser(description="Lexer test.")
    subparser = main_parser.add_subparsers(
        dest="command",
        required=True,
    )

    test_lexer_parser = subparser.add_parser("test_lexer", 
                                             help="Run the lexer test.")
    test_lexer_parser.set_defaults(func=test_lexer)

    test_pygments_parser = subparser.add_parser("test_pygments", 
                                                help="Run the pygments test.")
    test_pygments_parser.set_defaults(func=test_pygments)
    test_pygments_parser.add_argument('-x', '--xterm', action='store_true', 
                                      help='Use Terminal256Formatter for pygments output.')

    generate_parser = subparser.add_parser("generate", 
                                           help="Generate the theorical tokens.")
    generate_parser.set_defaults(func=generate_theorical_tokens)

    args = main_parser.parse_args()


    args.func(args)


if __name__ == "__main__":
    main()