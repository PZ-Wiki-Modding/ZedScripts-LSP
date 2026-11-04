import sys
import argparse
import typed_argparse as tap

from ZedScripts.server import zedserver
from ZedScripts.logger import initialize_logger

from ZedScripts.pygments.main import get_pygments_args_parser, runner_pygments


class Args(tap.TypedArgs):
    debug_port: int = tap.arg(default=5678, 
                              help="Port to run the server on")

def runner(args: Args) -> None:
    initialize_logger()

    debug_port = args.debug_port

    zedserver.startup(debug_port=debug_port)

def main() -> None:
    # deprecation support of launching without args
    args = sys.argv[1:]
    if len(args) == 0:
        print("DEPRECATED: use 'ZedScripts start' instead to launch the server")
        runner(Args())
        return

    tap.Parser(
        tap.SubParserGroup(
            tap.SubParser(
                "start",
                Args,
                help="start the ZedScripts language server"
            ),
            get_pygments_args_parser(sub="pygments"),
        ),
        prog="ZedScripts",
        description="""==========================
ZedScripts Language Server
==========================""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    ).bind(
        runner,
        runner_pygments,
    ).run()



if __name__ == "__main__":
    main()
