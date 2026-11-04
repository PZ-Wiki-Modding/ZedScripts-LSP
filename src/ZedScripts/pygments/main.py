from typing import overload
import typed_argparse as tap

class PygmentsArgs(tap.TypedArgs):
    file: str = tap.arg(positional=True, 
                        help="path to the file to be processed")
    xterm: bool = tap.arg("-x", "--xterm", default=False,
                          help="use Terminal256Formatter for pygments output.")
    tokens: bool = tap.arg("-t", "--tokens", default=False,
                          help="show the tokens instead of the highlighted code.")

def get_parser_help() -> str:
    return "Highlight ZedScripts code using Pygments."

@overload
def get_pygments_args_parser(*, sub: None = None, help: str = "__") -> tap.Parser: ...
@overload
def get_pygments_args_parser(*, sub: str) -> tap.SubParser: ...

def get_pygments_args_parser(sub: str | None = None, help: str = "highlight ZedScripts code using Pygments") -> tap.Parser | tap.SubParser:
    if sub is not None:
        return tap.SubParser(
            sub,
            PygmentsArgs,
            help=help,
        )
    return tap.Parser(
        PygmentsArgs, 
        description=help
    )


def runner_pygments(args: PygmentsArgs) -> None:
    from ZedScripts.pygments.lexer import ZedScriptsLexer, highlight_zedscripts
    from pygments.formatters import TerminalFormatter, Terminal256Formatter

    file = args.file
    with open(file, "r") as f:
        code = f.read()

    if args.tokens:
        for ttype, value in ZedScriptsLexer().get_tokens(code):
            print(ttype, repr(value))
    else:
        formatter = Terminal256Formatter() if args.xterm else TerminalFormatter()
        print(highlight_zedscripts(code, formatter))

def main():
    get_pygments_args_parser(help="[DEPRECATED] Use 'ZedScripts pygments' instead. Highlight ZedScripts code using Pygments.").bind(
        runner_pygments
    ).run()






if __name__ == "__main__":
    main()
