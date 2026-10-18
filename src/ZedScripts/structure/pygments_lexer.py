try:
    from pygments.lexer import RegexLexer, bygroups
    from pygments import token
    from pygments.formatter import Formatter
except ImportError:
    raise ImportError("Pygments is required to use this module, install the `pygments` group dependencies (`pip install ZedScripts[pygments]`).")


class ZedScriptsLexer(RegexLexer):
    name = "ZedScripts"
    aliases = ["zedscripts"]

    tokens = {
        "root": [
            (r'/\*', token.Comment.Multiline, 'comment'),

            (r"[,;:|!={}\[\]]", token.Operator),
            (r"(\S+[\S\/ ]*?)(\s*)(=)(\s*)",
             bygroups(
                 token.Name.Attribute,
                 token.Whitespace,
                 token.Operator,
                 token.Whitespace,
             )),
            (r"^(\s*)(\w+)(\s+)(|[\w !*.:\/]+?)(\s*)({)(\s*)$",
             bygroups(
                 token.Whitespace,
                 token.Keyword.Declaration,
                 token.Whitespace,
                 token.Name.Class,
                 token.Whitespace,
                 token.Operator,
                 token.Whitespace)),
            (r"(?<!\w)-?\d+\.\d+", token.Number.Float),
            (r"(?<!\w)-?\d+", token.Number.Integer),
            (r"\w+\.\w+", token.String.Double),
            # (r"\s+", token.Text),
            (r"[^\S\n]+", token.Whitespace),
            (r"\n", token.Whitespace),
            (r"[^\s,;:|!={}/]+", token.Text),
            (r"/(?!\*)", token.Text),
        ],
        'comment': [
            (r'[^*]+', token.Comment.Multiline),
            (r'\*/', token.Comment.Multiline, '#pop'),
            (r'\*', token.Comment.Multiline),
        ],
    }

def highlight_zedscripts(code: str, formatter: Formatter) -> str:
    from pygments import highlight

    return highlight(code, ZedScriptsLexer(), formatter)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Highlight ZedScripts code using Pygments.")
    parser.add_argument("file", 
                        help="Path to the ZedScripts file to highlight.")
    parser.add_argument("-x", "--xterm", action="store_true", 
                        help="Use Terminal256Formatter for pygments output.")
    parser.add_argument("-t", "--tokens", action="store_true",
                        help="Show the tokens instead of the highlighted code.")
    args = parser.parse_args()

    from pygments.formatters import TerminalFormatter, Terminal256Formatter

    with open(args.file, "r") as f:
        code = f.read()

    if args.tokens:
        for ttype, value in ZedScriptsLexer().get_tokens(code):
            print(ttype, value)
    else:
        formatter = Terminal256Formatter() if args.xterm else TerminalFormatter()
        print(highlight_zedscripts(code, formatter))

if __name__ == "__main__":
    main()