try:
    from pygments.lexer import RegexLexer, bygroups
    from pygments import token
    from pygments.formatter import Formatter
except ImportError:
    raise ImportError("Pygments is required to use this module, install the `pygments` group dependencies (`pip install ZedScripts[pygments]`).")


class ZedScriptsLexer(RegexLexer):
    """Pygments lexer for ZedScripts."""
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
