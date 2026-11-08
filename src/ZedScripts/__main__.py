import sys
import logging
import argparse
import typed_argparse as tap

from ZedScripts.server import zedserver
from ZedScripts.logger import initialize_logger

from ZedScripts.pygments.main import get_pygments_args_parser, runner_pygments


class MainArgs(tap.TypedArgs):
    debug_port: int = tap.arg(default=5678, 
                              help="Port to run the server on")
    stdio: bool = tap.arg("--stdio", default=False,
                          help="Use standard input/output for communication")

def runner(args: MainArgs) -> None:
    initialize_logger()

    debug_port = args.debug_port

    zedserver.startup(debug_port=debug_port)

def main() -> None:
    # deprecation support of launching without args
    args = sys.argv[1:]
    logging.log(logging.INFO, "Starting ZedScripts with args: %s", args)

    # if there are no args, or the first arg contains '-' '--', it
    # means there's no commands provided, so we default to running the server
    if len(args) == 0 or "--" in args[0] or "-" in args[0]:
        logging.warning("deprecated launch method: use 'ZedScripts start' command instead to launch the server. Extra arguments will be ignored.")
        runner(MainArgs())
        return

    tap.Parser(
        tap.SubParserGroup(
            tap.SubParser(
                "start",
                MainArgs,
                help="start the ZedScripts language server"
            ),
            get_pygments_args_parser(sub="pygments"),
        ),
        prog="ZedScripts",
        description="""==========================
ZedScripts Language Server
==========================

You can learn how to setup the ZedScripts LSP for your IDE in the extension's README: https://github.com/PZ-Wiki-Modding/ZedScripts-LSP.
        
LSP
---
You cannot use the LSP directly from the command line. You need to link it through your IDE which will handle the client-server communication.

    ZedScripts start

See the help menu for the details.
                
Pygments
--------
You can highlight script files directly from the command line using the 'pygments' subcommand.

    ZedScripts pygments <file>

See the help menu for the details.""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    ).bind(
        runner,
        runner_pygments,
    ).run()



if __name__ == "__main__":
    main()
